`compute` <-
function(expression = "", data, separate = FALSE) {
    colnames(data) <- toupper(colnames(data))
    pp <- translate(expression, data = data, tomatrix = FALSE)
    ppm <- do.call("rbind", lapply(pp, function(x) {
        xnames <- names(x)
        x <- unlist(lapply(x, paste, collapse = ","))
        names(x) <- xnames
        return(x)
    }))
    retain <- apply(ppm, 2, function(x) any(x >= 0))
    pp <- lapply(pp, function(x) x[retain])
    ppm <- ppm[, retain, drop = FALSE]
    data <- data[, retain, drop = FALSE]
    verify.qca(data)
    tempList <- vector("list", length(pp))
    for (i in seq(length(pp))) {
        x <- which(ppm[i, ] >= 0)
        val <- pp[[i]][x]
        temp <- data[, colnames(ppm)[x], drop = FALSE]
        for (j in seq(length(val))) {
            if (!is.numeric(temp[, j]) & possibleNumeric(temp[, j])) {
                temp[, j] <- asNumeric(temp[, j])
            }
            if (any(abs(temp[, j] - round(temp[, j])) >= .Machine$double.eps^0.5)) { 
                if (length(val[[j]]) > 1) {
                    cat("\n")
                    stop(simpleError("Multiple values specified for fuzzy data.\n\n"))
                }
                if (val[[j]] == 0) {
                    temp[, j] <- 1 - temp[, j]
                }
            }
            else { 
                temp[, j] <- as.numeric(temp[, j] %in% val[[j]])
            }
        }
        if (ncol(temp) > 1) {
            temp <- fuzzyand(temp)
        }
        tempList[[i]] <- temp
    }
    res <- as.data.frame(matrix(unlist(tempList), ncol = length(tempList)))
    colnames(res) <- rownames(ppm)
    if (ncol(res) > 1) {
        if (!separate) {
            res <- as.vector(fuzzyor(res))
        }
    }
    else {
        res <- as.vector(res[, 1])
    }
    return(res)
}
