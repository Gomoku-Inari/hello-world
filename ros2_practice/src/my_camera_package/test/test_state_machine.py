from my_camera_package.mode_state_machine import ModeStateMachine

def test_mode_state_machine_behavior():
    # コールバックが呼ばれた回数と中身を記録する配列（Mock）
    called_modes = []
    
    # 🌟 ROSのパブリッシュの代わりに、配列に文字をためるだけのダミーを注入
    dummy_callback = lambda mode: called_modes.append(mode)
    
    # 初期状態は "gray" でインスタンス化
    sm = ModeStateMachine(on_mode_changed_callback=dummy_callback, initial_mode="gray")
    
    # 【検証1】初期状態のゲッター確認
    assert sm.current_mode == "gray"
    assert len(called_modes) == 0  # まだ変化していないのでコールバックは0回
    
    # 【検証2】違うモード（color）を設定してみる
    sm.set_mode("color")
    assert sm.current_mode == "color"
    assert called_modes == ["color"]  # 🌟 ちゃんとエッジを検知して通知が1回飛んだか？
    
    # 【検証3】同じモード（color）をもう一度設定してみる（重複送信の抑止テスト）
    sm.set_mode("color")
    assert sm.current_mode == "color"
    assert called_modes == ["color"]  # ⚠️ 配列が増えていない（重複送信が安全に抑止されたか？）
    
    # 【検証4】他ノードからの同期処理テスト
    sm.sync_mode("face")
    assert sm.current_mode == "face"
    assert called_modes == ["color"]  # 🌟 同期処理（sync_mode）ではコールバックは発火しないか？
