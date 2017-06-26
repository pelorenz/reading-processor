`getNoflevels` <- function(data, conditions = "", outcome = "") {
    if (identical(conditions, "") & identical(outcome, "")) {
        if (is.null(colnames(data))) {
            colnames(data) <- c(LETTERS[ncol(data) - 1], "OUT")
            conditions <- LETTERS[ncol(data) - 1]
            outcome <- "OUT"
        }
        else {
            conditions <- colnames(data)[-ncol(data)]
            outcome <- colnames(data)[ncol(data)]   
        }
    }
    if (is.matrix(data)) {
        data <- as.data.frame(data)
    }
    if (identical(conditions, "")) {
        conditions <- setdiff(names(data), outcome)
    }
    dc.code <- unique(unlist(lapply(data, function(x) {
        if (is.numeric(x)) {
            return(x[x < 0])
        }
        else {
            return(as.character(x[x %in% c("-", "dc")]))
        }
    })))
    if (length(dc.code) == 0) {
        dc.code <- -1
    }
    else if (length(dc.code) > 1) {
        cat("\n")
        stop(simpleError("Multiple \"Don't care\" codes found.\n\n"))
    }
    data <- as.data.frame(lapply(data, function(x) {
        x <- as.character(x)
        x[x == dc.code] <- -1
        return(asNumeric(x))
    }))
    names(data) <- c(conditions, outcome)
    data[data < 0] <- -1
    fuzzy.cc <- apply(data[, conditions, drop=FALSE], 2, function(x) any(x %% 1 > 0))
    for (i in seq(length(conditions))) {
        if (!fuzzy.cc[i]) {
            copy.cc <- data[, i]
            if (any(copy.cc < 0)) {
                copy.cc[copy.cc < 0] <- max(copy.cc) + 1
                data[, i] <- copy.cc
            }
        }
    }
    noflevels <- apply(data[, conditions, drop=FALSE], 2, max) + 1
    noflevels[noflevels == 1] <- 2
    noflevels[fuzzy.cc] <- 2
    return(list(data = data, fuzzy.cc = fuzzy.cc, dc.code = dc.code, noflevels = as.numeric(noflevels)))
}
