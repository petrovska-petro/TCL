def test_constructor(TCL, pool, manager):
    tcl = manager.deploy(TCL, pool)
    assert tcl.pool() == pool