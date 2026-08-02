from pathlib import Path

from cogs.logs import load_logs_config, save_logs_config, get_configured_log_channel_id


def test_logs_config_persists_selected_channel(tmp_path: Path):
    config_path = tmp_path / "logs_config.json"

    config = load_logs_config(config_path)
    assert config == {}

    save_logs_config({"123456789": "987654321"}, config_path)
    assert load_logs_config(config_path) == {"123456789": "987654321"}
    assert get_configured_log_channel_id(123456789, config_path) == "987654321"
    assert get_configured_log_channel_id(999999999, config_path) is None
