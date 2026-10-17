PYTHON ?= python

.PHONY: help setup demo chat eval compare interop test

help:
	@echo "Các lệnh khả dụng cho StudyMate:"
	@echo "  make setup   - Khởi tạo và tạo chỉ mục bài giảng offline"
	@echo "  make demo    - Chạy kịch bản Demo 3 tầng tự động theo rubric"
	@echo "  make chat    - Bật giao diện trò chuyện trực tiếp (CLI)"
	@echo "  make eval    - Chạy bộ đánh giá Benchmark (Lab 5)"
	@echo "  make compare - [BONUS +1] So sánh 2 cấu hình RAG (Dense-only vs Hybrid)"
	@echo "  make interop - [BONUS +1] Chạy Client thứ hai kiểm chứng MCP Interoperability"
	@echo "  make test    - Chạy toàn bộ 4 file kiểm thử trong tests/"

setup:
	$(PYTHON) tools/build_index.py

demo:
	$(PYTHON) -m studymate.main --demo

chat:
	$(PYTHON) -m studymate.main

eval:
	$(PYTHON) -m studymate.eval.run_eval

compare:
	$(PYTHON) -m studymate.eval.run_eval --compare

interop:
	$(PYTHON) scripts/mcp_client_interop.py

test:
	$(PYTHON) -m tests.test_corpus
	$(PYTHON) -m tests.test_search
	$(PYTHON) -m tests.test_mcp
	$(PYTHON) -m tests.test_agent
