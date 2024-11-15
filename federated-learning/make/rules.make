.PHONY: release
release: $(RELEASE_BUNDLE)

$(RELEASE_BUNDLE): dist/wheels dist/install.sh
> @echo "    -o- Building release package v$(PROJECT_VERSION) -o-"
> @RELEASE_PASSWORD="$(RELEASE_PASSWORD)" makeself --ssl-encrypt --ssl-pass-src env:RELEASE_PASSWORD dist 'federated-learning_v$(PROJECT_VERSION).run' 'Federated Learning v$(PROJECT_VERSION)' ./install.sh
> @echo ""
> @echo "    -o- Done -o-"
> @echo ""
> @echo " => Send the following file: $@ <="
> @echo "    Password: $(RELEASE_PASSWORD)"
> @echo ""

dist/wheels: $(WHEEL)
> @rm -f dist/wheels/*_predict-*.whl dist/wheels/*_egegl-*.whl
> @tox -e dl-deps -- --dest-dir '$@' --filter 'elix-.*' --wheel '$<'
> @tox -e dl-deps -- --dest-dir '$@' --filter 'elix-.*' --wheel $@/elix_rdkit-*.whl
> @tox -e dl-deps -- --dest-dir '$@' --filter 'elix-.*' --wheel $@/elix_torch-*.whl
> @tox -e repack -- --delete --wheel $@/elix_rdkit-*.whl
> @tox -e repack -- --delete --wheel $@/elix_torch-*.whl
> @mv '$<' '$@'

dist/install.sh: assets/install.sh.tmpl src/federated_learning/version.py
> @echo "    -o- Generate install script v$(PROJECT_VERSION) -o-"
> @sed "s/@@@VERSION@@@/$(PROJECT_VERSION)/g" assets/install.sh.tmpl > "$@"
> @chmod 755 "$@"
