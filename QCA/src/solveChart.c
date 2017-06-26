# include <R.h>
# include <Rinternals.h>
# include <R_ext/Rdynload.h>
SEXP solveChart(SEXP chart, SEXP k) { 
    int *p_chart, *p_k, *p_result, *p_temp, *p_output, line;
    SEXP result, temp, output;
    SEXP usage = PROTECT(allocVector(VECSXP, 5));
    SET_VECTOR_ELT(usage, 0, chart = coerceVector(chart, INTSXP));
    SET_VECTOR_ELT(usage, 1, k = coerceVector(k, INTSXP));
    p_chart = INTEGER(chart);
    p_k = INTEGER(k);
    int rows = nrows(chart);
    int cols = ncols(chart);
    int colsums[cols];
    int nck;
    nck = 1;
    for (int i = 1; i <= p_k[0]; i++) {
        nck *= rows - (p_k[0] - i);
        nck /=  i;
    }
    SET_VECTOR_ELT(usage, 2, result = allocVector(INTSXP, nck));
    p_result = INTEGER(result);
    SET_VECTOR_ELT(usage, 3, temp = allocVector(INTSXP, p_k[0] * nck));
    p_temp = INTEGER(temp);
    int comb[p_k[0]];
    int e = 0;
    int h = p_k[0];
    int found = 0;
    for (int row = 0; row < nck; row++) {
        if (row == 0) {
            for (int i = 0; i < p_k[0]; i++) {
                comb[i] = i;
            }
        }
        else {
            if (e < rows - h) {
                h = 1;
                e = comb[p_k[0] - 1] + 1;
                comb[p_k[0] - 1] += 1;
            }
            else {
                e = comb[p_k[0] - h - 1] + 1;
                h++;
                for (int j = 0; j < h; j++) {
                    comb[p_k[0] - h + j] = e + j;
                }
            }
        }
        for (int col = 0; col < cols; col++) {
            colsums[col] = 0;
        }
        for (int r = 0; r < p_k[0]; r++) {
            line = comb[r];
            for (int col = 0; col < cols; col++) {
                colsums[col] += p_chart[col * rows + line];
            }
        }
        p_result[row] = 1; 
        for (int col = 0; col < cols; col++) {
            if (colsums[col] == 0) { 
                p_result[row] = 0;
            }
        }
        if (p_result[row] == 1) {
            for (int r = 0; r < p_k[0]; r++) {
                p_temp[p_k[0] * found + r] = comb[r];
            }
            found++;
        }
    }
    SET_VECTOR_ELT(usage, 4, output = allocMatrix(INTSXP, p_k[0], found));
    p_output = INTEGER(output);
    if (found > 0) {
        for (int f = 0; f < p_k[0] * found; f++) {
            p_output[f] = p_temp[f] + 1; 
        }
    }
    UNPROTECT(1);
    return(output);
}
