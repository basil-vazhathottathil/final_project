# AI Diagnostic Evaluation Results
_NACORE2026 — Paper ID 87_

## Summary Metrics

| Metric | Value |
| :--- | :---: |
| Diagnostic Accuracy | **76.2%** |
| Action Precision | 85.7% |
| Action Recall | 85.7% |
| Macro F1-Score | **85.7%** |
| False Positive Rate (escalation on DIY faults) | 0.0% |
| Avg LLM Confidence | 75.1% |

## Per-Scenario Results

| ID | Vehicle | Expected System | Agent Action | Conf. | Diag ✓ | Action ✓ |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| SCEN-P01 | 2018 Honda Civic | air flow | ASK | 0.80 | ✅ | ✅ |
| SCEN-P02 | 2020 Toyota Camry | fuel | ASK | 0.75 | ❌ | ✅ |
| SCEN-P03 | 2016 Ford F-150 | misfire | DIY | 0.80 | ✅ | ✅ |
| SCEN-P04 | 2019 BMW 3 Series | overtemp | ESCALATE | 1.00 | ❌ | ✅ |
| SCEN-P05 | 2017 Kia Sportage | fuel | ASK | 0.75 | ✅ | ✅ |
| SCEN-P06 | 2021 Nissan Altima | catalyst | DIY | 0.78 | ❌ | ✅ |
| SCEN-P07 | 2015 Chevrolet Malibu | voltage | DIY | 0.85 | ✅ | ✅ |
| SCEN-P08 | 2022 Hyundai Tucson | starter | ASK | 0.80 | ✅ | ✅ |
| SCEN-C01 | 2018 Toyota RAV4 | wheel speed | ASK | 0.80 | ✅ | ❌ |
| SCEN-C02 | 2020 Ford Explorer | traction | ASK | 0.80 | ✅ | ✅ |
| SCEN-C03 | 2016 Jeep Grand Cherokee | suspension | ASK | 0.70 | ❌ | ❌ |
| SCEN-B01 | 2019 Mercedes C-Class | airbag | ESCALATE | 0.95 | ✅ | ✅ |
| SCEN-B02 | 2017 Subaru Outback | lock | ASK | 0.70 | ✅ | ✅ |
| SCEN-B03 | 2021 Kia Sorento | AC | ASK | 0.80 | ❌ | ✅ |
| SCEN-U01 | 2020 Volvo XC90 | communication | ASK | 0.70 | ✅ | ✅ |
| SCEN-U02 | 2018 Audi A4 | ECM | ASK | 0.70 | ✅ | ❌ |
| SCEN-S01 | 2015 Honda CR-V | CV joint | ASK | 0.30 | ✅ | ✅ |
| SCEN-S02 | 2022 Toyota Highlander | tyre | ASK | 0.70 | ✅ | ✅ |
| SCEN-S03 | 2019 Mazda 3 | brake | ASK | 0.70 | ✅ | ✅ |
| SCEN-S04 | 2017 Ford Escape | alternator | ASK | 0.70 | ✅ | ✅ |
| SCEN-S05 | 2020 Hyundai Elantra | battery | ASK | 0.70 | ✅ | ✅ |
