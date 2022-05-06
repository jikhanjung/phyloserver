import tempfile
with tempfile.TemporaryDirectory() as tmpdirname:
    print('created temporary directory', tmpdirname)