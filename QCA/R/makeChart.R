`makeChart` <-
function(primes = "", configs = "", snames = "") {
    prmat <- is.matrix(primes)
    comat <- is.matrix(configs)
    if (prmat & comat) {
        if (!(is.numeric(primes) & is.numeric(configs))) {
            cat("\n")
            stop(simpleError("Matrices have to be numeric.\n\n"))
        }
        if (any(primes < 0) | any(configs < 0)) {
            cat("\n")
            stop(simpleError("Matrix values have to be non-negative.\n\n"))
        }
        if (any(apply(primes, 1, sum) == 0) | any(apply(configs, 1, sum) == 0)) {
            cat("\n")
            stop(simpleError("Matrices have to be specified at implicants level.\n\n"))
        }
        primes2 <- matrix(logical(length(primes)), dim(primes))
        primes2[primes > 0] <- TRUE
        mtrx <- sapply(seq(nrow(primes)), function(x) {
            apply(configs, 1, function(y) {
                all(primes[x, primes2[x, ]] == y[primes2[x, ]])
            })
        })
        if (nrow(configs) == 1) {
            mtrx <- matrix(mtrx)
        }
        else {
            mtrx <- t(mtrx)
        }
        rownames(mtrx) <- writePrimeimp(primes, collapse = "*",  uplow = all(primes < 3) | all(configs < 3))
        colnames(mtrx) <- writePrimeimp(configs, collapse = "*", uplow = all(primes < 3) | all(configs < 3))
        return(mtrx)
    }
    else if (!prmat & !comat) {
        tconfigs <- translate(configs, snames, tomatrix = FALSE)
        if (identical(snames, "")) {
            snames <- names(tconfigs[[1]])
        }
        tprimes <- translate(primes, snames, tomatrix = FALSE)
        mtrx <- matrix(FALSE, nrow=length(tprimes), ncol=length(tconfigs))
        for (i in seq(nrow(mtrx))) {
            for (j in seq(ncol(mtrx))) {
                tp <- unlist(tprimes[[i]])
                tc <- unlist(tconfigs[[j]])
                mtrx[i, j] <- all(tp[tp >= 0] == tc[tp >= 0])
            }
        }
        colnames(mtrx) <- names(tconfigs)
        rownames(mtrx) <- names(tprimes)
        return(mtrx)
    }
    else {
        cat("\n")
        stop(simpleError("Both arguments have to be matrices.\n\n"))
    }
}
