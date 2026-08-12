import argparse


def define_arguments_prompted(parser):
    parser.add_argument(
        "--model_type",
        choices=["GPT", "Claude", "Llama", "TogetherAI"],
        required=True,
        help="Model adapter to evaluate",
    )
    parser.add_argument("--model_name", help="Name of the model to evaluate", default='', required=True)
    parser.add_argument("--setting", choices=['base', 'enhanced'], help="base or enhanced setting", required=True)
    parser.add_argument("--prompt_type", choices=['InjecAgent', 'hwchase17_react'], help="prompt type", required=True)
    parser.add_argument("--only_first_step", default=False, action='store_true', help="Only predict the first step")
    parser.add_argument("--use_cache", default=False, action='store_true', help="Use existing dataset")
    parser.add_argument("--only_get_score", default=False, action='store_true', help="Only get score without inference")
    parser.add_argument(
        "--attack_method",
        "--attack-method",
        choices=["direct_request", "h_cot", "hang"],
        default="direct_request",
        help="Payload construction to evaluate",
    )
    parser.add_argument(
        "--harvested_trace_path",
        "--harvested-trace-path",
        default=None,
        help="Action-specific harvested-trace JSON; required for --attack-method hang",
    )
    parser.add_argument(
        "--use_harvested_trace",
        action="store_true",
        dest="legacy_use_harvested_trace",
        help=argparse.SUPPRESS,
    )
    parser.add_argument("--append_static_tool_execution", default=False, action='store_true',
                        help="Diagnostic only: append a fixed Action/Action Input to a HANG trace")
    parser.add_argument("--num_workers", type=int, default=1, help="Number of parallel workers for evaluation")
    
    
def define_arguments_finetuned(parser):
    parser.add_argument("--model_name", help="Name of the model to evaluate", required=True)
    parser.add_argument("--setting", choices=['base', 'enhanced'], help="base or enhanced setting", required=True)
    parser.add_argument("--prompt_type", choices=['InjecAgent', 'hwchase17_react'], help="prompt type", required=True)
    parser.add_argument("--only_first_step", action='store_true', help="Only predict the first step")
    
def parse_arguments(agent_type=None):
    parser = argparse.ArgumentParser()
    if agent_type == "prompted":
        define_arguments_prompted(parser)
    elif agent_type == "finetuned":
        define_arguments_finetuned(parser)
    args = parser.parse_args()
    params = args.__dict__
    if params.pop("legacy_use_harvested_trace", False):
        params["attack_method"] = "hang"
    return params
