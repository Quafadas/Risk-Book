// MathJax configuration for pymdownx.arithmatex in generic mode.
// Without this the $$...$$ blocks in docs/specs/ render as literal dollar signs.
window.MathJax = {
  tex: {
    inlineMath: [["\(", "\)"]],
    displayMath: [["\[", "\]"]],
    processEscapes: true,
    processEnvironments: true,
  },
  options: {
    ignoreHtmlClass: ".*|",
    processHtmlClass: "arithmatex",
  },
};

document$.subscribe(() => {
  MathJax.startup.output.clearCache();
  MathJax.typesetClear();
  MathJax.texReset();
  MathJax.typesetPromise();
});
