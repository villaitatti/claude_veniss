# Stop Hook — Final Summary

Output before ending the turn (≤15 lines):

1. **env:** dev | prod
2. **Resolved paths:** veniss_app, rs_source (or "absent")
3. **Changed:** files (classified)
4. **Commit:** suggested message (freeform imperative, repo style)
5. **PR:** title `{branch}: vX.Y.Z` + body (Summary / Related / Notes)
6. **Deploy:** commit → push → server `git pull` → RS reload (no build)
7. **SPARQL run:** count + path to audit log entry
8. **KPs / Resource Configs touched:** IRIs (or "none")
9. **Risks:** Blazegraph impact, broken bindings, missing predicates
