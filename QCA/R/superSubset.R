`superSubset` <-
function(data, outcome = "", conditions = "", relation = "nec", incl.cut = 1,
    cov.cut = 0, ron.cut = 0, pri.cut = 0, use.tilde = FALSE, use.letters = FALSE,
    depth = NULL, ...) {
    memcare <- FALSE 
    other.args <- list(...)
    colnames(data) <- toupper(colnames(data))
        neg.out <- FALSE
        if ("neg.out" %in% names(other.args)) {
            neg.out <- other.args$neg.out
        }
    incl.cut <- incl.cut - .Machine$double.eps ^ 0.5
    if (cov.cut > 0) {
        cov.cut <- cov.cut - .Machine$double.eps ^ 0.5
    }
    outcome <- toupper(outcome)
    if (substring(outcome, 1, 1) == "~") {
        neg.out <- TRUE
        outcome <- substring(outcome, 2)
    }
    if (! toupper(curlyBrackets(outcome, outside=TRUE)) %in% toupper(colnames(data))) {
        cat("\n")
        stop(simpleError("Inexisting outcome name.\n\n"))
    }
    if (grepl("\\{|\\}", outcome)) {
        outcome.value <- curlyBrackets(outcome)
        outcome <- curlyBrackets(outcome, outside=TRUE)
        data[, toupper(outcome)] <- as.numeric(data[, toupper(outcome)] %in% splitstr(outcome.value))
    }
    if (identical(conditions, "")) {
        conditions <- names(data)[-which(names(data) == outcome)]
    }
    else {
        conditions <- splitstr(conditions)
    }
    conditions <- toupper(conditions)
    verify.data(data, outcome, conditions)
    if (!(nec(relation) | suf(relation) | relation %in% c("sufnec", "necsuf"))) {
        cat("\n")
        stop(simpleError("The relationship should be \"necessity\", \"sufficiency\", \"sufnec\" or \"necsuf\".\n\n"))
    }
    relationcopy <- relation
    if (relation %in% c("sufnec", "necsuf")) {
        cov.cut <- incl.cut
    }
    if (relation == "sufnec") {
        relation <- "sufficiency"
    }
    else if (relation == "necsuf") {
        relation <- "necessity"
    }
    colnames(data) <- toupper(colnames(data))
    conditions <- replacements <- toupper(conditions)
    outcome <- toupper(outcome)
    data <- data[, c(conditions, outcome)]
    nofconditions <- length(conditions)
    if (neg.out) {
        data[, outcome] <- 1 - data[, outcome]
    }
    uplow <- !use.tilde
    fc <- apply(data[, conditions], 2, function(x) any(x %% 1 > 0))
    if (mv.data <- any(data[, conditions] > 1)) {
        uplow <- use.tilde <- FALSE
    }
    alreadyletters <- sum(nchar(conditions)) == length(conditions)
    collapse <- ifelse(alreadyletters & uplow | use.tilde, "", "*")
    if (use.letters & !alreadyletters) {
        replacements <- LETTERS[seq(length(conditions))]
        names(replacements) <- conditions
        colnames(data)[seq(length(conditions))] <- conditions <- replacements
        collapse <- ifelse(!uplow | use.tilde, "*", "")
    }
    noflevels <- apply(data[, conditions], 2, max) + 1L
    noflevels[fc] <- 2
    mbase <- c(rev(cumprod(rev(noflevels + 1L))), 1)[-1]
    noflevels[noflevels == 1] <- 2 
    if (is.null(depth)) {
        depth <- nofconditions
    }
    CMatrix <- .Call("superSubset",
                     as.matrix(data[, conditions]),
                     noflevels,
                     as.numeric(fc),
                     data[, outcome],
                     as.numeric(nec(relation)),
                     incl.cut,
                     cov.cut,
                     depth, PACKAGE = "QCA")
    colnames(CMatrix[[1]]) <- c("incl", ifelse(nec(relation), "RoN", "PRI"), "cov.r")
    colnames(CMatrix[[2]]) <- c("incl", ifelse(nec(relation), "RoN", "PRI"), "cov.r")
    prev.result <- FALSE
    lexpressions <- nrow(CMatrix[[1]])
    if (lexpressions > 0) {
        result.matrix <- CMatrix[[3]]
        rownames(result.matrix) <- expressions <- seq(lexpressions)
        colnames(result.matrix) <- conditions
        prev.result <- TRUE
        row_names <- writePrimeimp(result.matrix, collapse=collapse, uplow=uplow, use.tilde=use.tilde)
        rownames(CMatrix[[1]]) <- row_names
        result <- as.data.frame(CMatrix[[1]])
        mins <- CMatrix[[5]]
    }
    lexprnec <- 0
    if (nec(relation)) {
        lexprnec <- nrow(CMatrix[[2]])
        if (lexprnec + lexpressions == 0) {
            cat("\n")
            stop(simpleError(paste("\nThere are no combinations with incl.cut = ", round(incl.cut, 3), " and cov.cut = ", round(cov.cut, 3), "\n\n", sep="")))
        }
        if (lexprnec > 0) {
            result.matrix2 <- CMatrix[[4]]
            rownames(result.matrix2) <- seq(lexprnec) + lexpressions
            colnames(result.matrix2) <- conditions
            row_names2 <- writePrimeimp(result.matrix2, collapse="+", uplow=uplow, use.tilde=use.tilde)
            rownames(CMatrix[[2]]) <- row_names2
            mins2 <- CMatrix[[6]]
            if (prev.result) {
                result <- rbind(result, as.data.frame(CMatrix[[2]]))
                row_names <- c(row_names, row_names2)
                result.matrix <- rbind(result.matrix, result.matrix2)
                mins <- cbind(mins, mins2)
            }
            else {
                result <- as.data.frame(CMatrix[[2]])
                expressions <- seq(lexprnec)
                row_names <- row_names2
                result.matrix <- result.matrix2
                mins <- mins2
            }
        }
    }
    if (lexprnec + lexpressions == 0) {
        cat("\n")
        stop(simpleError(paste("There are no combinations with incl.cut = ", round(incl.cut, 3), " and cov.cut = ", round(cov.cut, 3), "\n\n", sep="")))
    }
    colnames(mins) <- rownames(result)
    rownames(mins) <- rownames(data)
    mins <- as.data.frame(mins)
    if (relationcopy == "sufnec") {
        colnames(result) <- c("inclS", "PRI", "inclN")
    }
    else if (relationcopy == "necsuf") {
        colnames(result) <- c("inclN", "PRI", "inclS")
    }
    if (nec(relation)) {
        tokeep <- result[, "RoN"] >= ron.cut
    }
    else {
        tokeep <- result[, "PRI"] >= pri.cut
    }
    result <- result[tokeep, , drop = FALSE]
    mins <- mins[, tokeep, drop = FALSE]
    if (nrow(result) == 0) {
        cat("\n")
        stop(simpleError(paste("There are no combinations with", ifelse(nec(relation), paste("ron.cut =", round(ron.cut, 3)), paste("pri.cut =", round(pri.cut, 3))), "\n\n")))
    }
    out.list <- list(incl.cov=result, coms=mins, use.letters=use.letters)
    if (use.letters & !alreadyletters) {
        out.list$letters=replacements
    }
    out.list$options <- list(
        outcome = outcome,
        neg.out = neg.out,
        conditions = conditions,
        relation = relation,
        incl.cut = incl.cut,
        cov.cut = cov.cut,
        use.tilde = use.tilde,
        use.letters = use.letters
    )
    return(structure(out.list, class="sS"))
}
