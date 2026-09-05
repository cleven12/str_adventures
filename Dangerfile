# Dangerfile — automated PR checks, run via `bundle exec danger` in CI.
# https://danger.systems/ruby/

# Warn on very large PRs — hard to review properly.
if git.lines_of_code > 500
  warn("This PR changes #{git.lines_of_code} lines — consider splitting it up.")
end

# Encourage a real PR description.
if github.pr_body.length < 10
  warn("Please add a description to this PR explaining what changed and why.")
end

# If an app's models.py changed, make sure a migration came with it.
changed_files = git.modified_files + git.added_files

apps_with_model_changes = changed_files
  .select { |f| f.match?(%r{^apps/[^/]+/models\.py$}) }
  .map { |f| f.split("/")[1] }
  .uniq

apps_with_model_changes.each do |app|
  migration_added = changed_files.any? { |f| f.start_with?("apps/#{app}/migrations/") }
  unless migration_added
    warn("`apps/#{app}/models.py` changed but no new migration was added under `apps/#{app}/migrations/`.")
  end
end
