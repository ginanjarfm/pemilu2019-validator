# PEMILU 2019 VALIDATOR

## Background

"Pemilu 2019" is the first Indonesia's election that voters will set of to the pools to elect both President and Legislatives at the same time.

KPU's work must be hard this time. Final official results will be announced in a month. Besides several quick count results, KPU publish real counting progress and the digital scan of form C1 result is also available on web. This tools is created to help KPU to validate their progress.

## Purpose

This is a tools to validate KPU announcement from `https://pemilu2019.kpu.go.id/#/ppwp/hitung-suara/`.

## Feature

Feature | Description
--- | ---
Counting process validation | Validate `"Hitung Suara"` result
Dump Data | Activate flag `DUMP_API`
Save Failure Validation | Activate flag `SAVE_LOG`
Save Failure Validation Image | Activate flag `SAVE_IMAGE`

## Example Findings

```text
[VALIDATION] VALIDATE SUMATERA BARAT => KOTA BUKITTINGGI => AUR BIRUGO TIGO BALEH => BIRUGO => TPS 19
[VALIDATION] [FAILED 3]: sum of candidates and total pool mismatch
[VALIDATION] sum of candidates: 152
[VALIDATION] pool total: 132
{"pemilih_j": 179, "suara_sah": 132, "ts": "2019-04-19 23:00:03", "chart": {"21": 19, "22": 133}, "suara_tidak_sah": 1, "suara_total": 133, "images": ["13926-19-C-XXX-X5.jpg", "13926-19-C-XXX-X6.jpg"], "pengguna_j": 133}
```

## Task List

- [x] Counting process validation
- [ ] Final result validation
- [ ] Display result as static html
- [x] Save findings and C1 files when validation FAILED
- [x] Continue from last validation step

## License

[MIT](https://raw.githubusercontent.com/ginanjarfm/pemilu2019-validator/master/LICENSE)

### ***DISCLAIMER***

Announcement on KPU's web is just an **INFORMATION** and counting process will be done **MANUALLY**. But we have to make sure that KPU's data is still **ACCURATE**.