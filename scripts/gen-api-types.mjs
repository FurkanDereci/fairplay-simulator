// `src/fairplay_simulator/web/api-types.d.ts`'i OpenAPI şemasından üretir.
//
// Şema **koddan** gelir: `python -m fairplay_simulator.cli export-openapi`. Böylece tip dosyası
// elle yazılmaz ve `docs-sync` testi (tests/test_docs_sync.py) OpenAPI yollarının dosyada
// bulunduğunu doğrular (ADR-0019). Sanal ortam etkinken koşulur: `npm run gen:api-types`.
import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";

import openapiTS, { astToString } from "openapi-typescript";

const OUT = "src/fairplay_simulator/web/api-types.d.ts";

const spec = execFileSync(
  "python3",
  ["-m", "fairplay_simulator.cli", "export-openapi", "--db", ":memory:"],
  { encoding: "utf8" },
);

const ast = await openapiTS(JSON.parse(spec), {
  exportType: true,
  alphabetical: true,
});
writeFileSync(OUT, astToString(ast));
console.log(`yazıldı: ${OUT}`);
