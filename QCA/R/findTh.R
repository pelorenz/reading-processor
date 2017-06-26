`findTh` <-
function(x, n = 1, hclustm = "complete", distm = "euclidean", ...) {
    other.args <- list(...)
        if ("groups" %in% names(other.args)) {
            n <- other.args$groups - 1
        }
    x <- sort(x)
    cutpoints <- cumsum(rle(cutree(hclust(dist(x, method = distm), method = hclustm), k = n + 1))[[1]])
    values <- rep(NA, n)
    for (i in seq(length(values))) {
        values[i] <- mean(x[seq(cutpoints[i], cutpoints[i] + 1)])
    }
    return(values)
}
