from pathlib import Path

path = Path("internal/agent/agent.go")
s = path.read_text()

old = '"github.com/charmbracelet/crush/internal/message"\n\t"github.com/charmbracelet/crush/internal/pubsub"'
new = '"github.com/charmbracelet/crush/internal/message"\n\t"github.com/charmbracelet/crush/internal/omega"\n\t"github.com/charmbracelet/crush/internal/pubsub"'
assert old in s, "agent import seam moved"
s = s.replace(old, new, 1)

old = '\ttools              *csync.Slice[fantasy.AgentTool]\n\n\tisSubAgent'
new = '\ttools              *csync.Slice[fantasy.AgentTool]\n\tcognitiveRuntime   omega.Runtime\n\n\tisSubAgent'
assert old in s, "sessionAgent field seam moved"
s = s.replace(old, new, 1)

old = '\tTools                []fantasy.AgentTool\n\tNotify               pubsub.Publisher[notify.Notification]'
new = '\tTools                []fantasy.AgentTool\n\tCognitiveRuntime     omega.Runtime\n\tNotify               pubsub.Publisher[notify.Notification]'
assert old in s, "SessionAgentOptions seam moved"
s = s.replace(old, new, 1)

old = '''func NewSessionAgent(
\topts SessionAgentOptions,
) SessionAgent {
\treturn &sessionAgent{
'''
new = '''func NewSessionAgent(
\topts SessionAgentOptions,
) SessionAgent {
\tcognitiveRuntime := opts.CognitiveRuntime
\tif cognitiveRuntime == nil {
\t\tcognitiveRuntime = omega.NoopRuntime{}
\t}
\treturn &sessionAgent{
'''
assert old in s, "NewSessionAgent seam moved"
s = s.replace(old, new, 1)

old = '\t\ttools:                csync.NewSliceFrom(opts.Tools),\n\t\tisYolo:'
new = '\t\ttools:                csync.NewSliceFrom(opts.Tools),\n\t\tcognitiveRuntime:     cognitiveRuntime,\n\t\tisYolo:'
assert old in s, "constructor field seam moved"
s = s.replace(old, new, 1)

old = '''\tsystemPrompt := a.systemPrompt.Get()
\tpromptPrefix := a.systemPromptPrefix.Get()
\tvar instructions strings.Builder
'''
new = '''\tsystemPrompt := a.systemPrompt.Get()
\tpromptPrefix := a.systemPromptPrefix.Get()

\t// EntityOS seam: compile the bounded current cognitive field before this
\t// model organ is invoked. The selected Crush provider/model is observed as
\t// causal route evidence; OMEGA does not dispatch or override it here.
\t// NoopRuntime renders an empty frame, preserving upstream Crush behavior.
\tframe, frameErr := a.cognitiveRuntime.Compile(ctx, omega.TurnInput{
\t\tSessionID: call.SessionID,
\t\tRunID:     call.RunID,
\t\tPrompt:    call.Prompt,
\t\tRoute: omega.OrganRoute{
\t\t\tKind:       "provider",
\t\t\tOrganID:    "crush-model",
\t\t\tAdapterID:  "crush-native",
\t\t\tProviderID: largeModel.ModelCfg.Provider,
\t\t\tModelID:    largeModel.ModelCfg.Model,
\t\t},
\t})
\tif frameErr != nil {
\t\treturn nil, fmt.Errorf("omega cognitive compile failed: %w", frameErr)
\t}
\tif cognitiveContext := frame.RenderSystemContext(); cognitiveContext != "" {
\t\tif systemPrompt != "" {
\t\t\tsystemPrompt += "\\n\\n"
\t\t}
\t\tsystemPrompt += cognitiveContext
\t}

\tvar instructions strings.Builder
'''
assert old in s, "Run compile seam moved"
s = s.replace(old, new, 1)

old = '''\t}()

\thistory, files := a.preparePrompt(msgs, largeModel.CatwalkCfg.SupportsImages, call.Attachments...)
'''
new = '''\t}()

\t// Reentry is deliberately registered after RunComplete's defer so it runs
\t// first (LIFO). A reentry failure therefore becomes the terminal turn error
\t// observed by the existing Crush completion path instead of being hidden.
\tdefer func() {
\t\treentryCtx, reentryCancel := context.WithTimeout(context.WithoutCancel(ctx), 5*time.Second)
\t\tdefer reentryCancel()
\t\toutcome := omega.TurnOutcome{
\t\t\tSessionID: call.SessionID,
\t\t\tRunID:     call.RunID,
\t\t\tCancelled: errors.Is(retErr, context.Canceled) || ctx.Err() != nil,
\t\t}
\t\tif currentAssistant != nil {
\t\t\toutcome.Text = currentAssistant.Content().String()
\t\t}
\t\tif retErr != nil {
\t\t\toutcome.Err = retErr.Error()
\t\t}
\t\tif reentryErr := a.cognitiveRuntime.Reenter(reentryCtx, frame, outcome); reentryErr != nil && retErr == nil {
\t\t\tretErr = fmt.Errorf("omega cognitive reentry failed: %w", reentryErr)
\t\t}
\t}()

\thistory, files := a.preparePrompt(msgs, largeModel.CatwalkCfg.SupportsImages, call.Attachments...)
'''
assert old in s, "Reentry seam moved"
s = s.replace(old, new, 1)

path.write_text(s)
