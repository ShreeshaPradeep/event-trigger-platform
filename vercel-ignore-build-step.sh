#!/bin/bash

echo "🔎 Checking if build is required..."

if [[ "$VERCEL_GIT_COMMIT_REF" == "staging" || "$VERCEL_GIT_COMMIT_REF" == "main" ]]; then
  echo "✅ Build can proceed"
  exit 1;
else
  echo "🛑 Build skipped"
  exit 0;
fi 