import json
import sys
from ortools.sat.python import cp_model

def solve_tree_memory_map(config_file):
    # --- 1. JSONファイルの読み込み ---
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    except Exception as e:
        print(f"[-] ファイルの読み込みに失敗しました: {e}")
        sys.exit(1)

    ram_ranges = config_data["ram_ranges"]
    box_hierarchy = config_data["box_hierarchy"]
    mem_configs = config_data["mem_configs"]

    model = cp_model.CpModel()

    # インスタンスの展開 (count分複製)
    all_units = []
    for config in mem_configs:
        for i in range(config["count"]):
            unit = config.copy()
            unit["id"] = f"{config['name']}_{i}"
            all_units.append(unit)

    print(f"[+] 総メモリユニット数 (展開後): {len(all_units)} 個")

    all_groups = set(g for u in all_units for g in u["groups"])
    all_boxes = list(box_hierarchy.keys())

    # --- 2. ツリー解析用ヘルパー関数 ---
    def get_root_ram(box_name):
        current = box_name
        while current in box_hierarchy:
            current = box_hierarchy[current]
        return current

    def get_ancestors(box_name):
        ancestors = []
        current = box_name
        while current in box_hierarchy:
            ancestors.append(current)
            current = box_hierarchy[current]
        return ancestors

    # --- 3. 変数の作成 ---
    unit_vars = {}
    for u in all_units:
        uid = u["id"]
        ram_name = get_root_ram(u["parent"])
        ram = ram_ranges[ram_name]

        start = model.NewIntVar(ram["start"], ram["end"], f'{uid}_s')
        end = model.NewIntVar(ram["start"], ram["end"], f'{uid}_e')
        interval = model.NewIntervalVar(start, u["size"], end, f'{uid}_i')
        
        unit_vars[uid] = {"start": start, "end": end, "interval": interval, "ram": ram_name}

        # アラインメント
        k = model.NewIntVar(0, ram["end"], f'{uid}_k')
        model.Add(start == k * u["align"])

    box_vars = {}
    for bname in all_boxes:
        ram_name = get_root_ram(bname)
        ram = ram_ranges[ram_name]
        b_start = model.NewIntVar(ram["start"], ram["end"], f'{bname}_s')
        b_end = model.NewIntVar(ram["start"], ram["end"], f'{bname}_e')
        box_vars[bname] = {"start": b_start, "end": b_end, "ram": ram_name}

    # --- 4. 制約の定義 ---
    # 包含関係
    for u in all_units:
        uid = u["id"]
        pbox = u["parent"]
        model.Add(unit_vars[uid]["start"] >= box_vars[pbox]["start"])
        model.Add(unit_vars[uid]["end"] <= box_vars[pbox]["end"])

    for bname, p_name in box_hierarchy.items():
        if p_name in box_vars:
            model.Add(box_vars[bname]["start"] >= box_vars[p_name]["start"])
            model.Add(box_vars[bname]["end"] <= box_vars[p_name]["end"])
        else:
            ram = ram_ranges[p_name]
            model.Add(box_vars[bname]["start"] >= ram["start"])
            model.Add(box_vars[bname]["end"] <= ram["end"])

    # Alloc状態の伝播
    box_active = {g: {b: model.NewBoolVar(f'act_{g}_{b}') for b in all_boxes} for g in all_groups}
    for g in all_groups:
        for u in all_units:
            if g in u["groups"]:
                for ancestor in get_ancestors(u["parent"]):
                    model.Add(box_active[g][ancestor] == 1)

    # 重なり禁止
    for g in all_groups:
        for ram_name in ram_ranges.keys():
            intervals_to_check = []
            for u in all_units:
                uid = u["id"]
                if unit_vars[uid]["ram"] != ram_name:
                    continue
                
                is_unit_active = model.NewBoolVar(f'{uid}_act_{g}')
                if g in u["groups"]:
                    model.Add(is_unit_active == 1)
                else:
                    model.Add(is_unit_active == box_active[g][u["parent"]])
                
                opt_int = model.NewOptionalIntervalVar(
                    unit_vars[uid]["start"], u["size"], unit_vars[uid]["end"], 
                    is_unit_active, f'{uid}_oi_{g}'
                )
                intervals_to_check.append(opt_int)

            if len(intervals_to_check) > 1:
                model.AddNoOverlap(intervals_to_check)

    # --- 5. 目的関数 ---
    max_end = model.NewIntVar(0, max(r["end"] for r in ram_ranges.values()), 'max_end')
    all_ends = [unit_vars[u["id"]]["end"] for u in all_units]
    model.AddMaxEquality(max_end, all_ends)
    model.Minimize(max_end)

    # --- 6. ソルバーの実行 ---
    solver = cp_model.CpSolver()
    # 2000個規模用のチューニング
    solver.parameters.max_time_in_seconds = 180.0  # タイムアウトを3分に設定
    solver.parameters.log_search_progress = True   # コンソールにソルバーの探索進捗を出力

    print("[+] 最適化計算を開始します。しばらくお待ちください...")
    status = solver.Solve(model)

    # --- 7. 結果の表示（Markdownファイル出力 & コンソール通知） ---
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        print(f"\n[+] 最適なメモリマップを解決しました! (Status: {solver.StatusName(status)})")
        
        # 1. ソルバーの結果から実データを抽出
        resolved_boxes = {}
        for bname in all_boxes:
            resolved_boxes[bname] = {
                "start": solver.Value(box_vars[bname]["start"]),
                "end": solver.Value(box_vars[bname]["end"]),
                "units": [],
                "children": []
            }
            
        for u in all_units:
            uid = u["id"]
            pbox = u["parent"]
            s_val = solver.Value(unit_vars[uid]["start"])
            e_val = solver.Value(unit_vars[uid]["end"])
            resolved_boxes[pbox]["units"].append({
                "id": uid, "start": s_val, "end": e_val, "size": u["size"]
            })

        # 2. BOX同士の親子関係を構築
        ram_roots = {r_name: {"units": [], "children": []} for r_name in ram_ranges.keys()}
        for bname, p_name in box_hierarchy.items():
            if p_name in ram_ranges:
                ram_roots[p_name]["children"].append(bname)
            else:
                resolved_boxes[p_name]["children"].append(bname)

        # アドレス順にソート
        for bname in all_boxes:
            resolved_boxes[bname]["units"].sort(key=lambda x: x["start"])
            resolved_boxes[bname]["children"].sort(key=lambda x: resolved_boxes[x]["start"])
        for r_name in ram_ranges.keys():
            ram_roots[r_name]["children"].sort(key=lambda x: resolved_boxes[x]["start"])

        # 3. マークダウンテキスト生成用バッファ
        md_lines = []
        md_lines.append("# 👁️ 階層型メモリマップ最適化結果")
        md_lines.append(f"**ステータス**: `{solver.StatusName(status)}`  ")
        md_lines.append(f"**総解決ユニット数**: {len(all_units)} 個\n")

        # 再帰的なマークダウン木構造生成関数
        def build_md_tree(node_name, is_box, data_dict, indent_level=0):
            indent = "    " * indent_level
            
            if is_box:
                # BOXの情報を整理
                start_hex = f"`0x{data_dict['start']:08X}`"
                end_hex = f"`0x{data_dict['end']:08X}`"
                size_bytes = data_dict['end'] - data_dict['start']
                size_hex = f"`0x{size_bytes:X}`"
                
                # 折りたたみ（details）タグの追加
                md_lines.append(f"{indent}<details>")
                md_lines.append(f"{indent}<summary>📦 <b>{node_name}</b> (Addr: {start_hex} - {end_hex}, Size: {size_hex})</summary>")
                md_lines.append(f"{indent}<ul>")
                
                # 子要素（BOXとユニット）をアドレス順にマージしてソート
                sub_elements = []
                for c_box in data_dict["children"]:
                    sub_elements.append({"name": c_box, "is_box": True, "start": resolved_boxes[c_box]["start"], "data": resolved_boxes[c_box]})
                for u in data_dict["units"]:
                    sub_elements.append({"name": u["id"], "is_box": False, "start": u["start"], "data": u})
                
                sub_elements.sort(key=lambda x: x["start"])
                
                # 子要素を再帰的に生成（インデントレベルを+1）
                for elem in sub_elements:
                    md_lines.append(f"{indent}<li>")
                    build_md_tree(elem["name"], elem["is_box"], elem["data"], indent_level + 1)
                    md_lines.append(f"{indent}</li>")
                    
                md_lines.append(f"{indent}</ul>")
                md_lines.append(f"{indent}</details>")
            else:
                # メモリユニットの描画
                start_hex = f"`0x{data_dict['start']:08X}`"
                end_hex = f"`0x{data_dict['end']:08X}`"
                size_hex = f"`0x{data_dict['size']:X}`"
                md_lines.append(f"{indent}💾 <b>{node_name}</b> (Addr: {start_hex} - {end_hex}, Size: {size_hex})")

        # 4. 最上位RAM領域ごとにツリーを構築
        for r_name, r_info in ram_ranges.items():
            md_lines.append(f"## ⚙️ {r_name}")
            md_lines.append(f"- 物理アドレス範囲: `0x{r_info['start']:08X}` 〜 `0x{r_info['end']:08X}`\n")
            
            sub_elements = [{"name": c_box, "is_box": True, "start": resolved_boxes[c_box]["start"], "data": resolved_boxes[c_box]} for c_box in ram_roots[r_name]["children"]]
            
            for elem in sub_elements:
                build_md_tree(elem["name"], elem["is_box"], elem["data"], indent_level=0)
                md_lines.append("") # 改行

        # 5. マークダウンファイルへの書き出し
        output_md_filename = "memory_map_report.md"
        with open(output_md_filename, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))
            
        print(f"[+] 展開・非表示可能なマークダウンレポートを出力しました: '{output_md_filename}'\n")
        
    else:
        print("\n[-] 時間内に解が見つからなかったか、条件を満たす配置が不可能です。\n")

if __name__ == "__main__":
    # 実行コマンド: python3 solve_memory.py memory_config.json
    config_file = "memory_config.json" if len(sys.argv) < 2 else sys.argv[1]
    solve_tree_memory_map(config_file)
