# Install

```text
/plugin marketplace add igormcsouza/house-style
/plugin install house-style@house-style
```

1. **Turn on auto-update (once):** `/plugin` > Marketplaces > house-style > **Enable auto-update**. It is off by default for third-party marketplaces; without it you never receive new rules.
2. Inside a project: `/house-style:init`.

## Updates

There is no pinned `version`: every merge to `main` is a new plugin version (its commit SHA). With auto-update on, changes arrive after your first message plus up to about 10 minutes; run `/reload-plugins` to apply them in the running session.

| Goal | Command |
|---|---|
| Manual update | `/plugin marketplace update house-style`, then `claude plugin update house-style@house-style` (both are needed) |
| Stay on a milestone | `/plugin marketplace add igormcsouza/house-style#v0.1.0` |
| Develop the plugin | `/plugin marketplace add ~/Projects/house-style`, or `claude --plugin-dir ~/Projects/house-style` for one session |
