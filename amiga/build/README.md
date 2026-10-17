# Building the public disk images

```sh
pip install amitools
cp network.example.ini network.ini     # never commit network.ini
python3 build_public.py --package a600       --config network.ini --out out/
python3 build_public.py --package airprintps --config network.ini --out out/
```

`build_public.py`:
1. copies the package tree;
2. fills `@@PRINTER_NAME/HOST/PORT/PATH@@`;
3. rejects bad values, such as leading zeros, which AmiTCP would read as octal;
4. for A600AirPrint, regenerates `Hulp/Doel-31.lst` and `Doel-32.lst` (the CRC lists that Installeer step [4] checks);
5. writes `Docs/SHA256.txt`;
6. builds an FFS ADF with the script protection bit set;
7. reads every file back from the ADF.

**Reproducibility.**
- The *files* are reproducible: the same configuration gives the same `Docs/SHA256.txt`.
- The ADF *image* is not byte-reproducible, because xdftool writes the current time into the file headers. Compare the files, not the image.
- With the original home configuration, the build reproduced all 36 files of the tested A600AirPrint package byte for byte. For AirPrintPS, the 24 shared files were identical; the public variant leaves out the Pi fallback and its part of LeesMij.
