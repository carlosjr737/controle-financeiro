def test_importa_entrypoints():
    import deploy.main
    import deploy.fechar_mes_main
    assert hasattr(deploy.main, "rodar_ciclo")
    assert hasattr(deploy.fechar_mes_main, "rodar_fechamento")
