#!/usr/bin/env bash
# CI guard: runs checkers and page test suites against the files a build
# workflow has just rewritten, BEFORE that workflow commits them.
#
# Why: the build workflows push with the Actions token (GITHUB_TOKEN), and
# a push made that way never starts another workflow. So "Test the page"
# and the check workflows never ran on a bot commit, and a rebuilt file
# that broke a test reached main unseen (test_calendar.js, from commit
# 6781dac on 2026-11-12, until PR #214). See docs/claude/conventions.md,
# "CI guard".
#
# Usage, from the repository root:
#   tools/ci_guard.sh test_derbies test_nearme check_derbies ...
# A name starting with test_ runs tools/<name>.js in headless Chromium
# (Playwright from /tmp/pw/node_modules, as in test-pages.yml); a name
# starting with check_ runs tools/<name>.py. Every name is run, even
# after a failure, so the summary lists them all. Exits 1 if any failed.
set -u

failed=()
passed=()
for name in "$@"; do
  log="/tmp/guard_${name}.log"
  case "$name" in
    test_pwa)
      mkdir -p /tmp/site/Football /tmp/pwa
      git ls-files -z | xargs -0 cp --parents -t /tmp/site/Football
      cmd=(node tools/test_pwa.js /tmp/site /tmp/pwa) ;;
    test_routes)
      mkdir -p /tmp/routes
      cmd=(node tools/test_routes.js . /tmp/routes) ;;
    test_*)
      cmd=(node "tools/${name}.js" .) ;;
    check_derbies)
      cmd=(python3 tools/check_derbies.py --full) ;;
    check_*)
      cmd=(python3 "tools/${name}.py") ;;
    *)
      echo "ci_guard: unknown name '$name'" >&2
      failed+=("$name (unknown name)")
      continue ;;
  esac

  echo "::group::${name}"
  start=$(date +%s)
  if NODE_PATH=/tmp/pw/node_modules "${cmd[@]}" > "$log" 2>&1; then
    status=passed; passed+=("$name")
  else
    status=FAILED; failed+=("$name")
  fi
  tail -n 60 "$log"
  echo "::endgroup::"
  echo "${name}: ${status} ($(( $(date +%s) - start )) s)"
done

if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
  {
    echo "## CI guard (run before the commit step)"
    echo
    echo "Passed: ${passed[*]:-none}"
    echo
    echo "Failed: ${failed[*]:-none}"
    echo
    if [ ${#failed[@]} -gt 0 ]; then
      echo "Nothing was committed or pushed: the commit step is skipped when the guard fails."
      echo
      for name in "${failed[@]}"; do
        f="/tmp/guard_${name%% *}.log"
        [ -f "$f" ] || continue
        echo "### ${name}"
        echo
        echo '```'
        tail -c 20000 "$f"
        echo '```'
      done
    fi
  } >> "$GITHUB_STEP_SUMMARY"
fi

if [ ${#failed[@]} -gt 0 ]; then
  echo "CI guard failed: ${failed[*]}. The commit step will not run."
  exit 1
fi
echo "CI guard passed: ${passed[*]}"
