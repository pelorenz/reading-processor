# include <R.h>
# include <Rinternals.h>
# include <R_ext/Rdynload.h>
SEXP truthTable(SEXP x, SEXP y, SEXP fuz, SEXP vo) { 
    int i, j, k, index;
    double *p_x, *p_inclpri, *p_vo, min, so, sumx, sumpmin, prisum, temp1, temp2;
    int xrows, xcols, yrows, ncut, *p_y, *p_fuz;
    SEXP usage = PROTECT(allocVector(VECSXP, 4));
    SET_VECTOR_ELT(usage, 0, x = coerceVector(x, REALSXP));
    SET_VECTOR_ELT(usage, 1, y = coerceVector(y, INTSXP));
    SET_VECTOR_ELT(usage, 2, fuz = coerceVector(fuz, INTSXP));
    SET_VECTOR_ELT(usage, 3, vo = coerceVector(vo, REALSXP));
    xrows = nrows(x);
    yrows = nrows(y);
    xcols = ncols(x);
    double copyline[xcols];
    p_x = REAL(x);
    p_y = INTEGER(y);
    p_fuz = INTEGER(fuz);
    p_vo = REAL(vo);
    SEXP inclpri = PROTECT(allocMatrix(REALSXP, 3 + xrows, yrows));
    p_inclpri = REAL(inclpri);
    so = 0;
    for (i = 0; i < length(vo); i++) {
        so += p_vo[i];
    }
    for (k = 0; k < yrows; k++) { 
        sumx = 0;
        sumpmin = 0;
        prisum = 0;  
        ncut = 0;
        for (i = 0; i < xrows; i++) { 
            min = 1000;
            for (j = 0; j < xcols; j++) { 
                copyline[j] = p_x[j * xrows + i];
                index = j * yrows + k;
                if (p_fuz[j] == 1) { 
                    if (p_y[index] == 0) {
                        copyline[j] = 1 - copyline[j];
                    }
                }
                else {
                    if (p_y[index] != (copyline[j])) {
                        copyline[j] = 0;
                    }
                    else {
                        copyline[j] = 1;
                    }
                }
                if (copyline[j] < min) {
                    min = copyline[j];
                }
            } 
            sumx += min;
            sumpmin += (min < p_vo[i])?min:p_vo[i];
            temp1 = (min < p_vo[i])?min:p_vo[i];
            temp2 = 1 - p_vo[i];
            prisum += (temp1 < temp2)?temp1:temp2;
            ncut += (min > 0.5)?1:0;
            p_inclpri[k*(3 + xrows) + 3 + i] = min;
        } 
        p_inclpri[k*(3 + xrows) + 0] = ncut;
        p_inclpri[k*(3 + xrows) + 1] = sumpmin/sumx;
        p_inclpri[k*(3 + xrows) + 2] = (sumpmin - prisum)/(sumx - prisum);
    } 
    UNPROTECT(2);
    return(inclpri);
}
