# CI/dev environment for 3d-models.
#
# The org's CI runs on self-hosted NixOS runners (`ryzen`, `beefy-actions`),
# and the runners deliberately provide almost nothing beyond `nix`, `git` and
# docker. Every tool a workflow shells out to comes from THIS file, entered
# via `nix develop` — that is what keeps repos with conflicting toolchains
# able to share the same runner machines: each repo's dependencies live in
# the nix store keyed by hash, isolated by construction, instead of being
# installed globally on the runner.
#
# So: if CI needs a new tool, add it to the matching devShell below. Never
# `sudo apt-get install` (NixOS runners have no apt or sudo), never
# `actions/setup-node`/`actions/setup-python` (their prebuilt tarballs
# hardcode FHS paths and their tool manifests match against an Ubuntu
# release), never ask for the tool to be added to the runner's own package
# set.
{
  description = "3d-models — dev and CI toolchain";

  # nixpkgs-unstable: the same channel the runner hosts are built from.
  # The pin here is independent — flake.lock in this repo decides what CI
  # actually gets, and bumping it is this repo's own decision. NOTE: bumping
  # the lock can bump OpenSCAD, which invalidates the render cache and
  # triggers a full (slow) re-render; update .openscad-version when it does.
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems
        (system: f nixpkgs.legacyPackages.${system});
    in
    {
      devShells = forAllSystems (pkgs:
        let
          # admesh is not in nixpkgs. Build it from the release tarball —
          # NOT the git tag, which ships no generated ./configure.
          admesh = pkgs.stdenv.mkDerivation (finalAttrs: {
            pname = "admesh";
            version = "0.98.5";
            src = pkgs.fetchurl {
              url = "https://github.com/admesh/admesh/releases/download/v${finalAttrs.version}/admesh-${finalAttrs.version}.tar.gz";
              hash = "sha256-DXmUv6WHxOlYsqx8fS+5DftsVGPTJROtoWnPcQpDhTU=";
            };
          });

          # Headless OpenSCAD: plain `openscad` is GLX-only and renders
          # 0-byte PNGs on the display-less runners (the old Xvfb + NVIDIA
          # EGL-pinning workarounds in build.yml existed for exactly this).
          # Wrap it to force the EGL/llvmpipe software path so PNG export
          # works with no X server at all. symlinkJoin keeps the wrapper
          # cheap — openscad itself comes straight from the binary cache.
          openscadHeadless = pkgs.symlinkJoin {
            name = "openscad-headless";
            paths = [ pkgs.openscad-unstable ];
            nativeBuildInputs = [ pkgs.makeWrapper ];
            postBuild = ''
              test -e ${pkgs.mesa}/share/glvnd/egl_vendor.d/50_mesa.json
              test -d ${pkgs.mesa}/lib/dri
              wrapProgram $out/bin/openscad \
                --set LIBGL_ALWAYS_SOFTWARE true \
                --set LIBGL_DRIVERS_PATH ${pkgs.mesa}/lib/dri \
                --set __EGL_VENDOR_LIBRARY_FILENAMES ${pkgs.mesa}/share/glvnd/egl_vendor.d/50_mesa.json \
                --prefix LD_LIBRARY_PATH : ${pkgs.mesa}/lib \
                --set-default QT_QPA_PLATFORM offscreen \
                --unset DISPLAY
            '';
          };
        in
        {
          # Everything build.yml shells out to. mkShell's stdenv already
          # puts a C compiler, make, and the usual coreutils/grep/sed/awk/
          # find on PATH; git and systemd-run (capped-openscad.sh) are
          # runner-baseline.
          default = pkgs.mkShell {
            packages = [
              openscadHeadless
              admesh
            ] ++ (with pkgs; [
              # python3 plus every third-party module build.yml's inline
              # python and scripts/*.py import. These used to be pip-installed
              # from unpinned PyPI ranges into throwaway venvs on the runner
              # that holds the deploy AWS role and a write-scoped
              # GITHUB_TOKEN (issue #423). Taking them from nixpkgs makes
              # flake.lock the pin — hash-verified like every other CI tool.
              (python3.withPackages (ps: with ps; [
                jsonschema # meta.json / *.parameters.json schema validation
                trimesh # scripts/check_interference.py boolean intersection
                manifold3d # trimesh's boolean engine
                numpy # trimesh dep; imported directly by test_check_interference
                networkx # trimesh graph/repair optional backend
                scipy # trimesh graph/repair optional backend
              ]))
              nodejs_22 # WASM customizer smoke tests (scripts/*.mjs)
              imagemagick # montage/convert/identify for og-hero.png
              zip # per-project STL + source bundles (build.yml)
              qrencode
              awscli2 # S3 deploy + PR previews
            ]);

            # ImageMagick on NixOS has no distro type.xml, so fonts resolve
            # through fontconfig. Pin fontconfig to a font set this flake
            # owns so `-font Liberation-Sans` (og-hero, issue #352) works
            # identically on every runner.
            FONTCONFIG_FILE = pkgs.makeFontsConf {
              fontDirectories = [ pkgs.liberation_ttf ];
            };
          };

          # Small shell for notify-failures.yml, which only needs gh (plus
          # the stdenv basics). Separate from `default` so those jobs don't
          # pay for the OpenSCAD/ImageMagick/AWS closure.
          scripts = pkgs.mkShell {
            packages = with pkgs; [
              gh
            ];
          };

          # Operator-run photogrammetry pipeline (scripts/scan_pipeline.py).
          # NOT used by CI — same spirit as scripts/render_view.py. CPU-only:
          # colmap here has no CUDA (nixpkgs' colmapWithCuda is not in the
          # binary cache), so dense reconstruction goes through OpenMVS.
          scan = pkgs.mkShell {
            packages = with pkgs; [
              colmap
              openmvs
              ffmpeg
              (python3.withPackages (ps: with ps; [
                numpy
                opencv4
                rembg
                trimesh
                manifold3d # trimesh boolean engine for scan_reference.py's slab-hull union
                scipy
                networkx
              ]))
            ];
          };
        });
    };
}
