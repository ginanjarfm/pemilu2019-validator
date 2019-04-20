# PEMILU 2019 VALIDATOR

## Background

"Pemilu 2019" is the first Indonesia's election that voters will set of to the pools to elect both President and Legislatives at the same time.

KPU's work must be hard this time. Final official results will be announced in a month. Besides several quick count results, KPU publish real counting progress and the digital scan of form C1 result is also available on web. This tools is created to help KPU to validate their progress.

## Purpose

This is a tools to validate KPU announcement from `https://pemilu2019.kpu.go.id/#/ppwp/hitung-suara/`.

## Feature

`$ python main.py -h`

Feature | Description
--- | ---
Counting process validation | Validate `"Hitung Suara"` result
Dump Data | Activate flag `dump_api`
Save Failure Validation | Activate flag `save_log`
Save Failure Validation Image | Activate flag `save_image`
Restart validation progress | Activate flag `restart`

## Validation Findings

*DATA PEMILIH DAN PENGGUNAAN HAK PILIH (**A**)*

URAIAN | JUMLAH
--- | ---
PEMILIH TERDAFTAR (DPT) | `{A1}`
PENGGUNA HAK PILIH | `{A2}`

*PEROLEHAN SUARA (**B**)*

| | URAIAN | SUARA SAH
--- | --- | ---
1 | (01) | `{B1}`
2 | (02) | `{B2}`

*JUMLAH SUARA SAH DAN TIDAK SAH (**C**)*

| | URAIAN | JUMLAH
--- | --- | ---
A | JUMLAH SELURUH SUARA SAH | `{C1}`
B | JUMLAH SUARA TIDAK SAH | `{C2}`
C | JUMLAH SELURUH SUARA SAH DAN SUARA TIDAK SAH | `{C3}`

### VALIDATION RESULT TYPE

Validation Failed Type | Example | Cause
--- | --- | ---
**[FAILED 1]** | `Total pool calculation mismatch!` | **`C1 + C2 != C3`**
| | `pool valid: {C1}` |
| | `pool invalid: {C2}` |
**[FAILED 2]** | `total DPT votes and total pool mismatch!` | **`C3 != A2`**
| | `DPT participation: {A2}` |
| | `pool total: {C3}` |
**[FAILED 3]** | `sum of candidates and valid pool mismatch!` | **`B1 + B2 != C1`**
| | `sum of candidates: {B1 + B2}` |
| | `pool valid: {C1}` |

### Example Findings

```text
[VALIDATION] VALIDATE SUMATERA BARAT => KOTA BUKITTINGGI => AUR BIRUGO TIGO BALEH => BIRUGO => TPS 19
[VALIDATION] [FAILED 3]: sum of candidates and valid pool mismatch
[VALIDATION] sum of candidates: 152
[VALIDATION] pool valid: 132
{"pemilih_j": 179, "suara_sah": 132, "ts": "2019-04-19 23:00:03", "chart": {"21": 19, "22": 133}, "suara_tidak_sah": 1, "suara_total": 133, "images": ["13926-19-C-XXX-X5.jpg", "13926-19-C-XXX-X6.jpg"], "pengguna_j": 133}
```

### Useful Command

Show validation error rate list [FAILED 3]:

```bash
grep -r -n -i --include="*.log" "DIFF 3" log
```

Total

```bash
grep -r -n -i --include="*.log" "DIFF 3" log | \
  while read -r line; do echo $(cut -d':' -f4 <<<"$line") >> temp; done && \
  sum=0; while read num; do ((sum += num)); done < temp; echo 'TOTAL DIFF 3:' $sum && rm temp
```

## Task List

- [x] Counting process validation
- [ ] Final result validation
- [ ] Display result as static html
- [x] Save findings and C1 files when validation FAILED
- [x] Continue from last validation step

## Suggestion to KPU

DATA ENTRY is the most critical activity. DATA ENTRY is also the first step to anything. DO VALIDATION since DATA ENTRY.

## License

[MIT](https://raw.githubusercontent.com/ginanjarfm/pemilu2019-validator/master/LICENSE)

### ***DISCLAIMER***

Announcement on KPU's web is just an **INFORMATION** and counting process will be done **MANUALLY**. But we have to make sure that KPU's data is still **ACCURATE**.