from pathlib import Path

path = Path("internal/agent/coordinator.go")
s = path.read_text()

old = '"github.com/charmbracelet/crush/internal/message"\n\t"github.com/charmbracelet/crush/internal/oauth"'
new = '"github.com/charmbracelet/crush/internal/message"\n\t"github.com/charmbracelet/crush/internal/omega"\n\t"github.com/charmbracelet/crush/internal/oauth"'
assert old in s, "coordinator omega import seam moved"
s = s.replace(old, new, 1)

old = '\trunComplete pubsub.Publisher[notify.RunComplete]\n\tinteractive bool\n\n\tcurrentAgent SessionAgent'
new = '\trunComplete      pubsub.Publisher[notify.RunComplete]\n\tinteractive      bool\n\tcognitiveRuntime omega.Runtime\n\n\tcurrentAgent SessionAgent'
assert old in s, "coordinator runtime field seam moved"
s = s.replace(old, new, 1)

old = '\tSkills      *skills.Manager\n\tInteractive bool\n}'
new = '\tSkills           *skills.Manager\n\tInteractive      bool\n\tCognitiveRuntime omega.Runtime\n}'
assert old in s, "CoordinatorOptions seam moved"
s = s.replace(old, new, 1)

old = '''\tskillTracker := skills.NewTracker(activeSkills)\n\n\tc := &coordinator{'''
new = '''\tskillTracker := skills.NewTracker(activeSkills)\n\n\t// EntityOS owns one top-level cognitive runtime below Crush sessions.\n\t// Direct coordinator tests/callers may inject a runtime. Normal app callers\n\t// get a portable file-backed state substrate under Crush's data directory.\n\tcognitiveRuntime := opts.CognitiveRuntime\n\tif cognitiveRuntime == nil {\n\t\tstatePath := omega.DefaultStatePath(opts.Config.Config().Options.DataDirectory)\n\t\tif statePath == "" {\n\t\t\tcognitiveRuntime = omega.NoopRuntime{}\n\t\t} else {\n\t\t\tpersistentRuntime, err := omega.NewPersistentRuntime(statePath)\n\t\t\tif err != nil {\n\t\t\t\treturn nil, fmt.Errorf("initialize omega persistent runtime: %w", err)\n\t\t\t}\n\t\t\tcognitiveRuntime = persistentRuntime\n\t\t}\n\t}\n\n\tc := &coordinator{'''
assert old in s, "NewCoordinator runtime construction seam moved"
s = s.replace(old, new, 1)

old = '\t\tinteractive:  opts.Interactive,\n\t}'
new = '\t\tinteractive:      opts.Interactive,\n\t\tcognitiveRuntime: cognitiveRuntime,\n\t}'
assert old in s, "coordinator literal seam moved"
s = s.replace(old, new, 1)

old = '''\tlargeProviderCfg, _ := c.cfg.Config().Providers.Get(large.ModelCfg.Provider)\n\tresult := NewSessionAgent(SessionAgentOptions{'''
new = '''\tlargeProviderCfg, _ := c.cfg.Config().Providers.Get(large.ModelCfg.Provider)\n\tcognitiveRuntime := c.cognitiveRuntime\n\tif isSubAgent {\n\t\t// Sub-agents are tools of the canonical top-level loop; they do not\n\t\t// independently mutate entity state. Their output reenters through the\n\t\t// top-level turn just like any other tool observation.\n\t\tcognitiveRuntime = omega.NoopRuntime{}\n\t}\n\tresult := NewSessionAgent(SessionAgentOptions{'''
assert old in s, "buildAgent runtime selection seam moved"
s = s.replace(old, new, 1)

old = '\t\tTools:                nil,\n\t\tNotify:               c.notify,'
new = '\t\tTools:                nil,\n\t\tCognitiveRuntime:     cognitiveRuntime,\n\t\tNotify:               c.notify,'
assert old in s, "buildAgent option seam moved"
s = s.replace(old, new, 1)

path.write_text(s)
