`allExpressions` <-
function(noflevels, arrange = FALSE, depth = NULL, raw = FALSE, ...) {
    aEmat <- createMatrix(noflevels + 1, arrange = arrange, depth = depth, ... = ...)
    return(structure(list(aE = aEmat - 1, raw = raw), class = "aE"))
}
