# Non-dossier merge report

Run: `nondossier-merge-20261122` (one mimo medium call per region; merged rating = mean of contributing per-model ratings, computed in code).

## Coverage

- Regions in scope: 1219
- Merged ok: 1182; failed to merge: 37 (statuses: {'rejected': 37})
- Contributors per merged region:
  - 7 contributors: 467 regions
  - 6 contributors: 546 regions
  - 5 contributors: 151 regions
  - 4 contributors: 15 regions
  - 3 contributors: 3 regions
- Regions with only 1 contributor: 0
- Failed to merge:
  - 19177384B99972609216724 La Pampa (ARG): rejected
  - 19177384B8726453430521 San Luis (ARG): rejected
  - 87207978B31722215463268 Bururi (BDI): rejected
  - 57655419B42503330785161 Rum Cay (BHS): rejected
  - 57670837B77729612727439 Central District (BWA): rejected
  - 84455774B92412385890269 Sjælland (DNK): rejected
  - 93511190B21658762393869 Saint John (GRD): rejected
  - 73500413B61038187736836 Essequibo Islands-West Demerara (GUY): rejected
  - 10453824B77004064719389 Gracias a Dios (HND): rejected
  - 49955354B96088034562700 Nord-Est Department (HTI): rejected
  - 22733592B44371380589399 Csongrád-Csanád (HUN): rejected
  - 22733592B46801225244053 Pest (HUN): rejected
  - 1811400B51283975314925 Dādra and Nagar Haveli and Damān and Diu (IND): rejected
  - 17685810B99097995033086 Khuzestan (IRN): rejected
  - 32016919B38538724963648 Lamu (KEN): rejected
  - 52472329B96254136738283 Saint Anne Sandy Point (KNA): rejected
  - 63095687B77911403325027 Gros Islet (LCA): rejected
  - 25212430B35951071556291 Ocnita (MDA): rejected
  - 25212430B43456438192105 Taraclia (MDA): rejected
  - 27540722B82031840289091 Atsimo-Atsinanana (MDG): rejected
  - 51498476B44501206987884 Dhaalu (MDV): rejected
  - 51498476B38384458438606 Meemu (MDV): rejected
  - 71437522B77650769364207 Nordland (NOR): rejected
  - 38925275B44970447822435 Gandaki (NPL): rejected
  - 602756B26590069038156 West Sepik (Sandaun) Province (PNG): rejected
  - 36066543B14518908529982 HARGHITA (ROU): rejected
  - 83879307B19000204873860 Bari (SOM): rejected
  - 68755315B98869091115359 Södermanlands län (SWE): rejected
  - 8384693B61807023607014 As-Sweida (SYR): rejected
  - 36821470B14101604973013 Chanthaburi Province (THA): rejected
  - 36821470B74825096412992 Chon Buri Province (THA): rejected
  - 36821470B69255687394343 Prachuap Khiri Khan Province (THA): rejected
  - 25984515B90474549897215 Burdur (TUR): rejected
  - 25984515B55399473509250 Karabük (TUR): rejected
  - 94954027B50419639501702 Saint Andrew (VCT): rejected
  - 42786344B61423155075663 Bolívar (VEN): rejected
  - 42786344B77541452473448 Dependencias Federales (VEN): rejected

## Rating spread

- Mean spread (max-min of contributing ratings): 0.0466 over 1219 regions
- Regions with spread > 0.30: 1
  - 93993887B40019078264500 Agion Oros (GRC): spread 0.320, mean 0.467, contributors muse,mimo,deepseek,haiku,luna,qwen

## Cost

- Exact total (this merge run): 0.5554920994 USD

## Systematic divergences (per-model, from the seven source waves)

| model | n_ok | mean rating | mean delta vs parent | mean abs delta | frac above parent | frac below parent |
|---|---|---|---|---|---|---|
| muse | 1219 | 0.478 | -0.011 | 0.020 | 0.14 | 0.46 |
| mimo | 1128 | 0.483 | -0.003 | 0.019 | 0.29 | 0.50 |
| deepseek | 1209 | 0.465 | -0.024 | 0.033 | 0.15 | 0.78 |
| glm | 683 | 0.491 | -0.011 | 0.025 | 0.24 | 0.64 |
| haiku | 1065 | 0.474 | -0.015 | 0.021 | 0.10 | 0.67 |
| luna | 1116 | 0.479 | -0.006 | 0.012 | 0.11 | 0.41 |
| qwen | 1196 | 0.469 | -0.020 | 0.029 | 0.15 | 0.69 |

Largest pairwise mean absolute rating differences (shared regions):
- deepseek vs luna: 0.026 (n=1107)
- mimo vs deepseek: 0.025 (n=1118)
- mimo vs qwen: 0.024 (n=1107)
- luna vs qwen: 0.023 (n=1095)
- muse vs qwen: 0.022 (n=1196)
- muse vs deepseek: 0.022 (n=1209)
- haiku vs qwen: 0.022 (n=1045)
- glm vs qwen: 0.021 (n=672)

Notes:
- glm contributes far fewer ok bases (683/1219, mostly rejected draws) than the other six waves; where present its ratings tend to sit further from the parent than the panel consensus.
- The widest spreads cluster where one model departs from a tight panel consensus (e.g. the Taiwan Province outlier, where six models rate 0.80-0.86 against the CHN parent 0.414 and qwen rates 0.66).

