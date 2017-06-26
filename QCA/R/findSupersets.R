`findSupersets` <-
function (noflevels, input, ...) {
    other.args <- list(...)
        if ("input.combs" %in% names(other.args)) {
            input <- other.args$input.combs
        }
    if (!is.matrix(input)) {
        if (!is.vector(input)) {
            cat("\n")
            stop("input must be either an solution-space matrix or a vector of line numbers.\n\n",
                 call. = FALSE)
        }
        else {
            if (any(input > prod(noflevels))) {
                cat("\n")
                stop(paste("Some line numbers do not belong in the solution-space for",
                           length(noflevels), "causal conditions.\n\n"), call. = FALSE)
            }
            input <- getRow(noflevels, input)
        }
    }
    mbase <- rev(c(1, cumprod(rev(noflevels))))[-1]
    allcombn <- t(createMatrix(rep(2, length(noflevels)))[-1, ])
    primes <- sort.int(unique(as.vector(apply(input, 1, function(x) (x*mbase) %*% allcombn + 1))))
    if (primes[1] == 1) {
        return(primes[-1])
    }
    else {
        return(primes)
    }
}
