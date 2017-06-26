`findSubsets` <-
function(noflevels, input, stop, ...) {
    other.args <- list(...)
        if ("row.no" %in% names(other.args)) {
            input <- other.args$row.no
        }
        if ("maximum" %in% names(other.args)) {
            stop <- other.args$maximum
        }
    stop <- ifelse(missing(stop), prod(noflevels), stop)
    result <- lapply(input, function(x) {
        .Call("findSubsets", x, noflevels - 1, rev(c(1, cumprod(rev(noflevels))))[-1], stop, PACKAGE="QCA")
    })
    return(sort(unique(unlist(result))))
}
