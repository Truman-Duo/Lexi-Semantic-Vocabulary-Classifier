"""Config subcommand."""

import argparse


def build_parser():
    parser = argparse.ArgumentParser(description="Lexi: 配置 AI API 设置")
    parser.add_argument("--api-key", help="设置 API 密钥")
    parser.add_argument("--api-base-url", help="设置 API 基础 URL")
    parser.add_argument("--model", help="设置模型名称")
    parser.add_argument("--show", action="store_true", help="显示当前配置")
    parser.add_argument("--api-config", help="配置文件路径")
    return parser


def handle_config(ctrl, argv):
    args = build_parser().parse_args(argv)
    if args.api_config: ctrl.load_config(args.api_config)
    if args.show:
        c = ctrl.config
        print(f"API Base URL: {c.api_base_url}")
        print(f"模型: {c.model}")
        print(f"API 密钥: {c.api_key[:8] + '...' if c.api_key else '(未设置)'}")
        return
    changed = False
    if args.api_key: ctrl.config.api_key = args.api_key; changed = True
    if args.api_base_url: ctrl.config.api_base_url = args.api_base_url; changed = True
    if args.model: ctrl.config.model = args.model; changed = True
    if changed:
        print(f"配置已保存: {ctrl.save_config(args.api_config)}")
    else:
        _interactive(ctrl)


def _interactive(ctrl):
    c = ctrl.config
    print("Lexi API 配置（按回车保留当前值）")
    k = input(f"API 密钥 [{_mask(c.api_key)}]: ").strip()
    if k: c.api_key = k
    u = input(f"API Base URL [{c.api_base_url}]: ").strip()
    if u: c.api_base_url = u
    m = input(f"模型 [{c.model}]: ").strip()
    if m: c.model = m
    print(f"配置已保存: {ctrl.save_config()}")


def _mask(key: str) -> str:
    return (key[:8] + "...") if key and len(key) > 8 else "(未设置)" if not key else "***"
