# Bao cao cac framework Text-to-SQL public sau DIN-SQL va MAC-SQL

Ngay lap: 2026-07-22

Pham vi: Bao cao nay tong hop cac framework Text-to-SQL co paper cong khai va lien quan truc tiep den pipeline sinh SQL hoan chinh, loai tru DIN-SQL va MAC-SQL vi da chay rieng. Trang thai source code duoc ghi theo kiem tra cong khai tai thoi diem lap bao cao.

## Ket luan nhanh

Neu muc tieu la chon baseline tiep theo de chay tren Spider/BIRD voi chi phi adapter hop ly, thu tu nen uu tien la:

1. C3SQL: de chay nhat, code gon, zero-shot ChatGPT pipeline.
2. DAIL-SQL: baseline ICL manh, public code ro, co self-consistency.
3. TA-SQL: framework hai stage canh chinh schema/logical synthesis, public code ro, gan voi bai toan hallucination.
4. CHESS: multi-agent pipeline day du va gan voi MAS, nhung setup nang hon do retrieval/index/schema pruning.
5. DeepEye-SQL: pipeline rat hoan chinh va hien dai, nhung la SIGMOD 2026, co the qua manh/qua moi so voi nhom baseline ban dau.

PARSQL va BASE-SQL nen de muc "watch/adapt later" vi source public hien tai chua chac du de reproduce ngay. SQL-PaLM co paper tot nhung khong public framework code day du, nen khong phu hop lam runnable baseline truc tiep.

## Bang tong hop

| Framework | Paper / venue | Kieu framework | Public source code | Muc do phu hop chay baseline |
|---|---|---|---|---|
| DAIL-SQL | Text-to-SQL Empowered by Large Language Models, PVLDB 17(5), 2024; DOI 10.14778/3641204.3641221 | Few-shot ICL + example selection + prompt organization + optional self-consistency | Co, official repo: https://github.com/BeachWang/DAIL-SQL | Cao |
| C3SQL | C3: Zero-shot Text-to-SQL with ChatGPT, arXiv 2023 | Zero-shot prompt pipeline: clear prompting, calibration with hints, consistent output | Co, official repo: https://github.com/bigbigwatermalon/C3SQL | Rat cao |
| CHESS | CHESS: Contextual Harnessing for Efficient SQL Synthesis, arXiv 2024 | Multi-agent retrieval, schema selection, candidate generation, unit testing | Co, repo: https://github.com/ShayanTalaei/CHESS | Cao nhung setup nang |
| TA-SQL | Before Generation, Align it!, Findings ACL 2024 | Task Alignment cho schema linking va logical synthesis | Co, official repo: https://github.com/quge2023/TA-SQL | Cao |
| PARSQL | Findings ACL 2025 | SQL parsing + reasoning + text-to-reason learning + SQL selection | Co repo toi thieu: https://github.com/yaxundai/parsql, nhung hien chi thay README/LICENSE | Trung binh/thap cho reproduce ngay |
| BASE-SQL | arXiv 2025, work in progress | Open-model SFT pipeline: schema linking, candidate generation, revision, merge revision | Repo cong khai: https://github.com/CycloneBoy/base_sql, nhung README con Todo publish code/model | Watch, chua nen uu tien |
| DeepEye-SQL | Proc. ACM Manag. Data / SIGMOD 2026; DOI 10.1145/3802035 | Software-engineering pipeline: grounding, schema linking, generation, debugging/revision, selection | Co, official repo: https://github.com/HKUSTDial/DeepEye-SQL | Cao nhung rat moi/nang |
| SQL-PaLM | TMLR 2024 | Few-shot prompting + instruction fine-tuning + execution-guided selection | Khong thay official public code day du; chi co output folder trong google-research | Thap cho runnable baseline |

## Taxonomy ngan

Co the nhin cac framework nay theo truc tien hoa: prompt tot hon -> retrieval/schema selection tot hon -> alignment va reasoning ro hon -> SFT/open-model -> software-engineering pipeline co testing/selection. Khong nen goi tat ca la multi-agent: DAIL-SQL va C3SQL chu yeu la prompt/ICL; TA-SQL la alignment; PARSQL la parsing/reasoning; BASE-SQL la SFT/open-model pipeline; CHESS va DeepEye-SQL moi that su gan voi orchestration/pipeline nhieu stage.

## 1. DAIL-SQL

DAIL-SQL la mot pipeline ICL tap trung vao viec toi uu cach dua thong tin vao LLM. Diem chinh cua no khong phai multi-agent, ma la systematic prompt engineering: cach bieu dien cau hoi/schema, cach chon example, cach sap xep example, va self-consistency voting.

Framework gom cac thanh phan chinh:

- Preprocess schema va dataset.
- Tao prompt theo nhieu kieu representation.
- Chon few-shot examples theo do tuong dong cau hoi va SQL skeleton/query.
- Goi LLM de sinh SQL.
- Tuy chon self-consistency: sinh nhieu ung vien SQL, dung execution/database feedback de bo phieu.

Diem dac biet: DAIL-SQL phu hop lam baseline manh vi no vua don gian hon agent framework, vua co ket qua cao tren Spider. Repo ghi nhan muc tieu token efficiency, vi prompt chi dua cac thong tin can thiet thay vi nhan ban day du schema cho moi example.

Source code: Co public official repo `BeachWang/DAIL-SQL`. Repo co script `run_dail_sql.sh`, `run_dail_sql_with_sc.sh`, `run_for_bird.sh`, cac module preprocess va call LLM. Paper PVLDB co artifact URL toi repo nay.

Nhan xet cho thuc nghiem hien tai: Nen chay sau C3SQL. Neu muon baseline prompt-ICL manh de so voi MAS pipeline, DAIL-SQL la ung vien tot hon nhom correction-only.

## 2. C3SQL

C3SQL la framework zero-shot Text-to-SQL voi ChatGPT. Paper public tren arXiv 2023; toi chua xac nhan venue peer-reviewed. C3 viet tat cho ba thanh phan:

- Clear Prompting: thiet ke prompt ro rang de dua schema/question vao model.
- Calibration with Hints: bo sung hint de giam sai lech model.
- Consistent Output: chuan hoa output SQL va co logic consistency.

Day la pipeline end-to-end don gian: nhan cau hoi + schema, goi ChatGPT/GPT API, xuat `predicted_sql.txt`, roi chay evaluation. No khong phai agent framework va khong co schema pruning/retrieval phuc tap nhu CHESS, nhung do do de adapter va de debug.

Diem dac biet: C3SQL phu hop lam baseline "zero-shot LLM" co paper, khac voi baseline direct prompt tu viet trong repo. No co code official gon, phu hop smoke test nhanh tren Spider.

Source code: Co public official repo `bigbigwatermalon/C3SQL`, MIT license. README co huong dan chuan bi Spider, chay `bash run_c3sql.sh`, va evaluation bang test-suite-sql-eval. Caveat: repo ghi ro huong dan hien chi ho tro Spider original database.

Nhan xet cho thuc nghiem hien tai: Nen uu tien dau tien neu can mot baseline public paper de chay nhanh sau DIN/MAC.

## 3. CHESS

CHESS la mot framework Text-to-SQL multi-agent/pipeline kha gan voi huong MAS. Paper public tren arXiv 2024; toi chua xac nhan venue peer-reviewed chinh thuc. No duoc thiet ke cho database lon, schema rong, can grounding vao database values va catalog/context.

Framework gom bon tac nhan/chuc nang chinh:

- Information Retriever: lay gia tri/cot/context lien quan tu database va catalog.
- Schema Selector: cat giam schema lon thanh sub-schema quan trong.
- Candidate Generator: sinh ung vien SQL va refine lap lai.
- Unit Tester: kiem tra ung vien bang natural-language unit tests va execution/functionality feedback.

Diem dac biet: CHESS xu ly bai toan scale va schema pruning rat ro. No khac DIN/DAIL o cho khong chi prompt engineering, ma co retrieval/indexing va schema selection truoc khi generation. No cung gan voi luan diem MAS vi co cac stage co the log va audit: retrieval, schema, candidate, validation.

Source code: Co repo public `ShayanTalaei/CHESS`. README mo ta preprocessing LSH/vector database va cac script chay main pipeline. Can OpenAI/GCP config tuy backend.

Nhan xet cho thuc nghiem hien tai: Rat dang chay neu paper cua minh nhan manh multi-stage/MAS. Tuy nhien setup nang hon C3SQL/DAIL-SQL vi can preprocess, index, va cau hinh backend.

## 4. TA-SQL

TA-SQL xuat phat tu bai toan hallucination trong Text-to-SQL. Tac gia cho rang cac framework hai stage thong thuong gom schema linking va logical synthesis van bi hallucination do LLM phai "generalize" qua nhieu buoc. Giai phap la Task Alignment: bien tung subtask thanh dang tac vu quen thuoc hon voi LLM.

Framework gom hai module chinh:

- TASL, Task-Aligned Schema Linking: canh chinh schema linking bang cach de model tao SQL gia/dummy SQL roi trich xuat schema entities lien quan.
- TALOG, Task-Aligned Logical Synthesis: canh chinh logical synthesis bang bieu dien trung gian gan voi workflow phan tich du lieu/Pandas-like API, sau do chuyen sang SQL.

Diem dac biet: TA-SQL phu hop voi de tai hallucination vi no phan loai va giam hallucination theo hai nhom schema-based va logic-based. Day la pipeline sinh SQL hoan chinh, khong chi sua SQL sau khi co prediction.

Source code: Co official repo `quge2023/TA-SQL`. README ghi ro accepted to Findings ACL 2024, co code implementation/evaluation TA-SQL tren BIRD dev, dung GPT-4 backend.

Nhan xet cho thuc nghiem hien tai: Nen chay neu muon baseline gan voi claim "schema/logical hallucination". Adapter co the can sua SDK OpenAI/Azure API va duong dan BIRD/Spider.

## 5. PARSQL

PARSQL la framework nham cai thien small language models cho Text-to-SQL bang SQL parsing va reasoning. Diem chinh la dung parser de trich constraints tu SQL, tao sub-SQLs cho data augmentation, sinh reasoning/explanation, va huan luyen text-to-reason/task multi-task.

Framework theo paper gom:

- PARSer: SQL parser trich dieu kien/constraints va tao sub-SQLs.
- Tao reason/explanation bang rule-based va LLM-based methods.
- Text-to-reason multi-task learning de giup SLM khong bo sot constraints.
- SQL selection dua tren do tuong dong giua generated SQL va reason.

Diem dac biet: PARSQL khong chi la prompt pipeline; no gan voi training va model adaptation. Phu hop so voi cac open/SFT baselines hon la prompt-only baselines.

Source code: ACL Anthology ghi "Code can be found" tai GitHub `yaxundai/parsql`. Tuy nhien khi kiem tra repo, hien chi thay README/LICENSE va 1 commit, chua thay code pipeline day du. Vi vay nen ghi trang thai la public placeholder/toi thieu, can kiem tra lai truoc khi dua vao ke hoach chay.

Nhan xet cho thuc nghiem hien tai: Khong nen uu tien neu can runnable baseline ngay. Nen de muc theo doi hoac lien he tac gia/kiem tra repo cap nhat.

## 6. BASE-SQL

BASE-SQL la pipeline dua tren open-source model fine-tuning, nham tao baseline manh nhung de trien khai hon cac he thong dong GPT-4. Paper/repo mo ta bon thanh phan:

- Schema Linking.
- Candidate SQL Generate.
- SQL Revision.
- SQL Merge Revision.

Diem dac biet: Huong nay dang chu y vi tap trung vao open model va chi phi. Paper claim su dung Qwen2.5-Coder-32B-Instruct, trung binh khoang 5 LLM calls cho moi cau hoi.

Source code: Co repo public `CycloneBoy/base_sql`, nhung README hien van co Todo "Organize the code and publish it to github" va "Release model". Do do khong nen xem la source code reproduce day du tai thoi diem nay.

Nhan xet cho thuc nghiem hien tai: Chi nen dua vao bang survey/literature. Chua nen dua vao batch baseline neu muc tieu la run duoc ngay.

## 7. DeepEye-SQL

DeepEye-SQL la framework rat moi theo huong "software-engineering-inspired Text-to-SQL", trong Proc. ACM Manag. Data / SIGMOD 2026. No xem Text-to-SQL nhu mot quy trinh phat trien/kiem thu phan mem thay vi mot lan prompt sinh SQL.

Pipeline gom:

- Value Retrieval / grounding gia tri lien quan tu database.
- Schema Linking ket hop nhieu tin hieu.
- SQL Generation sinh nhieu ung vien.
- SQL Revision bang checker-style debugging: syntax, execution, result-level repair.
- SQL Selection dua tren execution-aware selection.
- Snapshot workflow de checkpoint, resume, inspect, export va evaluate.

Diem dac biet: Day la pipeline day du va engineering hoa tot nhat trong danh sach. No ho tro Spider, BIRD va Spider2, co tests, docs, runbooks, results public. Ve mat thuc nghiem, no co the la baseline rat manh nhung cung co nguy co "qua moi" va khac generation so voi cac paper 2023-2025.

Source code: Co official repo `HKUSTDial/DeepEye-SQL`, README ghi SIGMOD 2026 va co cau truc `runner`, `docs`, `tests`, `results`.

Nhan xet cho thuc nghiem hien tai: Tot cho vong baseline nang/cap nhat. Neu paper cua minh so voi nhom 2025 tro ve truoc, can can nhac dua DeepEye-SQL vao phan "new strong baseline" thay vi baseline chinh.

## 8. SQL-PaLM

SQL-PaLM la framework cua Google Research, TMLR 2024. Paper gom ca few-shot prompting va instruction fine-tuning, execution-based filtering, selection tu nhieu paradigms, synthetic data, database content, va schema element selection.

Framework paper bao gom:

- Few-shot prompting va consistency decoding.
- Instruction fine-tuning tren data mo rong/da dang.
- Query-specific database content.
- Test-time selection voi execution feedback.
- Schema element selection cho database phuc tap.

Diem dac biet: SQL-PaLM la paper manh ve phan tich cac che do adaptation cua LLM cho Text-to-SQL, nhung phu thuoc model PaLM-2 noi bo trong thuc nghiem goc.

Source code: Google Research co folder `sql_palm`, nhung README noi folder nay show output SQL-PaLM tren Spider dev split; model dung trong paper la internal PaLM-2. Do do khong co full public runnable framework de reproduce nhu DAIL/C3/CHESS/TA-SQL.

Nhan xet cho thuc nghiem hien tai: Nen cite trong related work, khong nen chon lam baseline runnable.

## Nhom khong phai pipeline Text-to-SQL doc lap

Mot so paper/framework lien quan trong workspace khong nen xep cung nhom "pipeline T2SQL hoan chinh":

- SQLFixAgent: chu yeu la correction/review/refine sau khi CodeS sinh SQL ban dau. Stage `run_sqltool.py` la CodeS local, stage `run_fix.py` moi la agent fix.
- SCoT2S: self-correction Text-to-SQL, phu hop neu da co initial SQL.
- EMLC: multi-level correction, tap trung sua loi schema/skeleton/execution.
- DAC: decomposed automation correction, sua entity/skeleton.
- Text-to-SQL Error Correction with Code LMs: correction baseline, can input SQL ban dau.
- AmbiSQL: interactive ambiguity detection/resolution, phu hop intent/ambiguity hon la static Spider batch.

Nhom nay van co gia tri neu muc tieu cua paper la "failure attribution" hoac "repair pipeline", nhung khong nen dung de tra loi cau hoi "framework nao sinh SQL end-to-end nhu DIN/MAC".

## De xuat ke hoach chay tiep

### Smoke tier 1: baseline de adapter

1. C3SQL tren Spider dev subset n=50 hoac n=100.
2. DAIL-SQL voi cung subset, cung model va temperature.

Muc tieu: co hai baseline public paper, chi phi thap, log prompt/output ro.

### Smoke tier 2: pipeline gan MAS

3. TA-SQL tren BIRD dev mini hoac Spider neu adapter duoc prompt/data.
4. CHESS tren BIRD dev subset, vi CHESS thiet ke cho BIRD/large schema.

Muc tieu: so voi cac pipeline co schema linking, grounding, correction/validation ro.

### Heavy tier

5. DeepEye-SQL neu can mot strong modern baseline.
6. PARSQL/BASE-SQL chi khi repo/model artifacts da day du.

## Nguon da kiem tra

- DAIL-SQL GitHub: https://github.com/BeachWang/DAIL-SQL
- DAIL-SQL PVLDB PDF: https://www.vldb.org/pvldb/vol17/p1132-gao.pdf
- DAIL-SQL Papers With Code: https://paperswithcode.com/paper/text-to-sql-empowered-by-large-language
- C3SQL GitHub: https://github.com/bigbigwatermalon/C3SQL
- C3SQL arXiv: https://arxiv.org/abs/2307.07306
- C3SQL Papers With Code: https://paperswithcode.com/paper/c3-zero-shot-text-to-sql-with-chatgpt
- CHESS GitHub: https://github.com/ShayanTalaei/CHESS
- CHESS arXiv: https://arxiv.org/abs/2405.16755
- CHESS arXiv/DBLP: https://dblp.org/rec/journals/corr/abs-2405-16755
- Stanford LDR research page for CHESS/CHASE-SQL/Reasoning-SQL: https://ldr.stanford.edu/research/
- TA-SQL GitHub: https://github.com/quge2023/TA-SQL
- TA-SQL paper page: https://papers.cool/arxiv/2405.15307
- PARSQL ACL Anthology: https://aclanthology.org/2025.findings-acl.37/
- PARSQL GitHub: https://github.com/yaxundai/parsql
- BASE-SQL Papers With Code: https://paperswithcode.com/paper/base-sql-a-powerful-open-source-text-to-sql
- BASE-SQL arXiv: https://arxiv.org/abs/2502.10739
- BASE-SQL GitHub: https://github.com/CycloneBoy/base_sql
- DeepEye-SQL GitHub: https://github.com/HKUSTDial/DeepEye-SQL
- SQL-PaLM Google Research: https://research.google/pubs/sql-palm-improved-large-language-model-adaptation-for-text-to-sql/
- SQL-PaLM arXiv: https://arxiv.org/abs/2306.00739
- SQL-PaLM google-research folder: https://github.com/google-research/google-research/tree/master/sql_palm
