# CoT Forgery baseline prompt

`cot_forgery_prompt.yaml` is the qualified OpenAI prompt from the CoT Forgery
evaluation in
[`prompt-injection-as-role-confusion`](https://github.com/pndh/prompt-injection-as-role-confusion),
source commit `0af14644db45120963896c18bf2c2cf82162fad4`. It is included here
because the semantic-forgery generators load it directly.

CoT Forgery is a synthesized-trace baseline. It is not another name for HANG,
whose trace is harvested from a successful surrogate-model execution.

The copied prompt is distributed under the accompanying MIT license in
`LICENSE.md`.
