import asyncio
import logging
import dpath.util as dp
import json


class SemgrepService:
    """
    Сервис для проверки безопасности файлов
    """
    async def run_semgrep_check(self, file_path):
        try:
            logging.info(f"Semgrep scan of {file_path} is started.")
            process = await asyncio.create_subprocess_exec(
                "semgrep", file_path, "--json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                executable="/usr/local/bin/semgrep"
            )
            stdout, _ = await process.communicate()

            # конвертируем результаты в json и ищем impact
            data_str = stdout.decode("utf-8")
            data_dict = json.loads(data_str)
            values = dp.values(data_dict, "/results/**/impact")
            if "HIGH" in values:
                impact = "HIGH"
            elif "MEDIUM" in values:
                impact = "MEDIUM"
            elif "LOW" in values:
                impact = "LOW"
            else:
                impact = "NO IMPACT"
            logging.info(f"Semgrep scan of {file_path} is completed.")
            return {
                "data": data_str,
                "impact": impact
            }
        except Exception as e:
            logging.exception("Exception while running semgrep: %s", e)
            return None