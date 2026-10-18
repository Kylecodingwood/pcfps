#!/usr/bin/env bash
# Package PCFPS monorepo as source-only zip (excludes build artifacts and local data).
set -euo pipefail

scriptDirectory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repositoryRoot="$(cd "${scriptDirectory}/.." && pwd)"
dateStamp="$(date +%Y%m%d)"

if [[ $# -ge 1 ]]; then
  outputZipPath="$1"
else
  outputZipPath="$(cd "${repositoryRoot}/.." && pwd)/pcfps-source-${dateStamp}.zip"
fi

if [[ -f "${outputZipPath}" ]]; then
  echo "Removing existing archive: ${outputZipPath}"
  rm -f "${outputZipPath}"
fi

outputDirectory="$(dirname "${outputZipPath}")"
mkdir -p "${outputDirectory}"

echo "Packaging source from: ${repositoryRoot}"
echo "Output archive:       ${outputZipPath}"

cd "${repositoryRoot}"

zip -r "${outputZipPath}" . \
  -x "backend/target/*" \
  -x "backend/target/**/*" \
  -x "backend/.idea/*" \
  -x "backend/.idea/**/*" \
  -x "*.iml" \
  -x "frontend/node_modules/*" \
  -x "frontend/node_modules/**/*" \
  -x "frontend/dist/*" \
  -x "frontend/dist/**/*" \
  -x "outputfile/*" \
  -x "outputfile/**/*" \
  -x "terra_las/*" \
  -x "terra_las/**/*" \
  -x "*.joblib" \
  -x "frontend/.env" \
  -x ".DS_Store" \
  -x "**/.DS_Store" \
  -x ".git/*" \
  -x ".git/**/*" \
  -x ".cursor/*" \
  -x ".cursor/**/*" \
  -x "dist/pcfps-source*.zip" \
  -x "dist/*" \
  -x "dist/**/*"

echo ""
echo "Archive created successfully."
du -h "${outputZipPath}"
echo ""
echo "See SOURCE_README.md inside the archive for setup instructions."
