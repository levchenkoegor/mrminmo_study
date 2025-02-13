#!/bin/bash


# run the regression analysis
3dDeconvolve -input pb04.$subj.r*.scale+tlrc.HEAD                                            \
    -ortvec bandpass_rall.1D bandpass                                                        \
    -ortvec ROIPC.fsvent.r01.1D ROIPC.fsvent.r01                                             \
    -ortvec ROIPC.fsvent.r02.1D ROIPC.fsvent.r02                                             \
    -ortvec mot_demean.r01.1D mot_demean_r01                                                 \
    -ortvec mot_demean.r02.1D mot_demean_r02                                                 \
    -ortvec mot_deriv.r01.1D mot_deriv_r01                                                   \
    -ortvec mot_deriv.r02.1D mot_deriv_r02                                                   \
    -polort 4 -float                                                                         \
    -fout -tout -x1D X.xmat.1D -xjpeg X.jpg                                                  \
    -fitts fitts.$subj                                                                       \
    -errts errts.${subj}                                                                     \
    -x1D_stop                                                                                \
    -bucket stats.$subj

# -- use 3dTproject to project out regression matrix --
#    (make errts like 3dDeconvolve, but more quickly)
3dTproject -polort 0 -input pb04.$subj.r*.scale+tlrc.HEAD                                    \
           -ort X.xmat.1D -prefix errts.${subj}.tproject



