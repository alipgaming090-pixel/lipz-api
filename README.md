# Lipzx API Adapter

This project exposes `/gen` in the response shape expected by Lipzx.py.

Required Vercel Environment Variable:

UPSTREAM_API_URL = your authorized account API endpoint

Example request:
`/gen?name=laoe&count=1&region=BD&password_prefix=LIPZX&ghost=false&detect_rare=true`

Expected normalized response:
`{"accounts":[{"uid":"...","account_id":"...","password":"...","name":"...","region":"..."}],"attempts_made":1,"rare_count":0,"success":true,"total_created":1,"total_requested":1}`

The adapter does not create accounts itself. It only calls an upstream API that you control/are authorized to use and normalizes its response for Lipzx.py.
