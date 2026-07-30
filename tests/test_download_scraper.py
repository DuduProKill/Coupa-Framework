from modules.download_scraper import DownloadScraper


def test_analisar_arquivo_signature_and_behaviour(tmp_path):
    scraper = DownloadScraper(requisicoes=[], pasta_download=str(tmp_path))
    arquivo = tmp_path / 'sample.txt'
    arquivo.write_text('Orçamento conforme', encoding='utf-8')

    ok, result = scraper.analisar_arquivo(str(arquivo), '123', 'Orçamento teste')

    assert ok is False
    assert result == 'palavra'
