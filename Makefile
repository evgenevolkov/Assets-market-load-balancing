.PHONY: install start_generator_nginx start_generator_app start_analyzer \
		build_generator_container start_generator_container \
		stop_generator_container run_all_checks run_tests run_type_checks \
		run_linting clean

menu:
	@echo "Select an option:"; \
	select opt in "Start generator with Nginx" \
				  "Start generator as standalone app" \
				  "Start analyzer" "Build generator container" \
				  "Start generator container" "Stop generator container" \
				  "Run all checks" "Run tests" "Run type checks" \
				  "Run linting"  "Clean" "Exit"; do \
	    case $$opt in \
	        ("Start generator with Nginx") make start_generator_nginx; break;; \
	        ("Start generator as standalone app") make start_generator_app; break;; \
	        ("Start analyzer") make start_analyzer; break;; \
	        ("Build generator container") make build_generator_container; break;; \
	        ("Start generator container") make start_generator_container; break;; \
	        ("Stop generator container") make stop_generator_container; break;; \
	        ("Run all checks") make run_all_checks; break;; \
	        ("Run tests") make run_tests; break;; \
	        ("Run type checks") make run_type_checks; break;; \
			("Run linting") make run_linting; break;; \
	        ("Clean") make clean; break;; \
	        ("Exit") exit;; \
	        (*) echo "Invalid option";; \
	    esac; \
	done


install:
	python3 -m venv .venv
	./.venv/bin/pip install -r requirements.txt
	./.venv/bin/pip install -r requirements-dev.txt
	@mv prices_analyzer/.env.example prices_analyzer/.env
	@mv prices_generator/.env.example prices_generator/.env

start_generator_nginx:
	docker compose up --build

start_analyzer:
	cd prices_analyzer && ../.venv/bin/python -m app.app

start_generator_app:
	cd prices_generator && ../.venv/bin/uvicorn app.app:app --reload

build_generator_container:
	docker build -t prices_generator:latest -f prices_generator/Dockerfile .

start_generator_container:
	docker rm -f prices_generator || true
	docker run --name prices_generator -p 8000:8000 --env-file prices_generator/.env prices_generator 

stop_generator_container:
	docker stop prices_generator || true

run_all_checks: run_linting run_tests

run_tests:
	PYTHONPATH=$(shell pwd)/prices_generator pytest -s prices_generator/
	PYTHONPATH=$(shell pwd)/prices_analyzer pytest -s prices_analyzer/

run_type_checks:
	mypy prices_analyzer || true
	mypy prices_generator || true

run_linting:
	pylint . || true
	flake8 || true

clean:
	docker stop prices_generator || true
	docker rm prices_generator || true
	docker rmi prices_generator:latest || true

docker_prune:
	docker image prune -f || true