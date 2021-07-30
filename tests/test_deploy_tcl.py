def test_constructor(TCL, pool, manager, treasury):
    tcl = manager.deploy(TCL, pool, treasury)
    assert tcl.pool() == pool
    assert tcl.treasury() == treasury
