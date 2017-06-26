`findRows` <-
function(expression = "", ttobj, remainders = FALSE) {
    if (identical(expression, "")) {
        stop(simpleError("The expression is missing.\n\n"))
    }
    if (missing(ttobj)) {
        stop(simpleError("The truth table object is missing.\n\n"))
    }
    else {
        if (!is(ttobj, "tt")) {
            stop(simpleError("Argument \"ttobj\" is not a truth table object.\n\n"))
        }
    }
    noflevels <- ttobj$noflevels
    conditions <- ttobj$options$conditions
    trexp <- translate(paste(expression, collapse = "+"), snames = conditions, tomatrix = FALSE)
    result <- matrix(ncol = length(trexp[[1]]), nrow = 0)
    for (i in seq(length(trexp))) {
        rowi <- trexp[[i]]
        detected <- !unlist(lapply(rowi, function(x) identical(x, -1)))
        rowi <- rowi[detected]
        rowi <- expand.grid(rowi)
        if (sum(!detected) > 0) {
            restm <- createMatrix(noflevels[!detected])
            colnames(restm) <- conditions[!detected]
            rowi <- apply(rowi, 1, function(x) rep(x, each = nrow(restm)))
            for (r in seq(ncol(rowi))) {
                detm <- matrix(rowi[, r], nrow = nrow(restm))
                colnames(detm) <- conditions[detected]
                temp <- cbind(restm, detm)
                result <- rbind(result, temp[, conditions])
            }
        }
        else {
            result <- rbind(result, rowi)
        }
    }
    rows <- sort(unique(drop(rev(c(1, cumprod(rev(noflevels))))[-1] %*% t(result)) + 1))
    if (remainders) {
        rows <- setdiff(rows, ttobj$indexes)
    }
    return(rows)
}
