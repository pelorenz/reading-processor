`solveChart` <-
function(chart, row.dom = FALSE, all.sol = FALSE, ...) {
    if (!is.logical(chart)) {
        cat("\n")
        stop(simpleError("Use a T/F matrix. See makeChart's output.\n\n"))
    }
    other.args <- list(...)
    if ("min.dis" %in% names(other.args)) {
        if (is.logical(other.args$min.dis)) {
            all.sol <- !other.args$min.dis
        }
    }
    if (all.sol) {
        row.dom <- FALSE
    }
    row.numbers <- seq(nrow(chart))
    if (row.dom) {
        row.numbers <- rowDominance(chart)
        chart <- chart[row.numbers, ]
    }
    output <- list()
    if (all(dim(chart) > 1)) {
        k <- ceiling(sum(lpSolve::lp("min", rep(1, nrow(chart)), t(chart), ">=", 1)$solution))
        if (all.sol & k < nrow(chart)) {
            if (nrow(chart) > 29) { 
                cat("\n")
                stop(paste(strwrap("The PI chart is too large to identify all models.\n\n", exdent = 7), collapse = "\n", sep=""))
            }
            output <- .Call("allSol", k, chart * 1, PACKAGE="QCA")
            output[output == 0] <- NA
        }
        else {
            output <- .Call("solveChart", chart * 1, k, PACKAGE="QCA")
        }
    }
    else {
        output <- matrix(seq(nrow(chart)))
        if (ncol(chart) == 1) {
            output <- t(output)
        }
    } 
    return(matrix(row.numbers[output], nrow=nrow(output)))
}
