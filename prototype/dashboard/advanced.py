import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

from data_loading import all_data_from_variables


def render_advanced(st_obj, config):
    st_obj.write(f"Advanced...")

    # Some weather availability / capacity graphs
    [
        ASSUMPTIONS,
        DEMAND,
        NETWORK,
        STATISTICS,
        CUTOUT,
        SELECTION,
        EEZ,
        AVAIL_SOLAR,
        AVAIL_ONWIND,
        AVAIL_OFFWIND,
        AVAIL_CAPACITY_SOLAR,
        AVAIL_CAPACITY_ONWIND,
        AVAIL_CAPACITY_OFFWIND,
    ] = all_data_from_variables("../", config)

    with st_obj:
       col1, col2, col3 = st.columns([1, 1, 1])

    fig1 = plt.figure()
    fig2 = plt.figure()
    fig3 = plt.figure()
    gs1 = GridSpec(2, 1, figure=fig1)
    gs2 = GridSpec(2, 1, figure=fig2)
    gs3 = GridSpec(2, 1, figure=fig3)
    ax1 = fig1.add_subplot(gs1[0, 0])
    ax2 = fig2.add_subplot(gs2[0, 0])
    ax3 = fig3.add_subplot(gs3[0, 0])
    ax4 = fig1.add_subplot(gs1[1, 0])
    ax5 = fig2.add_subplot(gs2[1, 0])
    ax6 = fig3.add_subplot(gs3[1, 0])

    # Solar avail
    AVAIL_SOLAR.sel(dim_0=0).plot(cmap="Reds", ax=ax1)
    SELECTION.plot(ax=ax1, edgecolor="k", color="None")
    CUTOUT.grid.plot(ax=ax1, color="None", edgecolor="grey", ls=":")
    ax1.set_title("SOLAR AVAIL")

    # Wind (onshore) avail
    AVAIL_ONWIND.sel(dim_0=0).plot(cmap="Greens", ax=ax2)
    SELECTION.plot(ax=ax2, edgecolor="k", color="None")
    CUTOUT.grid.plot(ax=ax2, color="None", edgecolor="grey", ls=":")
    ax2.set_title("WIND ONSHORE AVAIL")

    # Wind (offshore) avail
    AVAIL_OFFWIND.sel(dim_0=0).plot(cmap="Blues", ax=ax3)
    SELECTION.plot(ax=ax3, edgecolor="k", color="None")
    CUTOUT.grid.plot(ax=ax3, color="None", edgecolor="grey", ls=":")
    ax3.set_title("WIND OFFSHORE AVAIL")

    # Capacity factors
    AVAIL_CAPACITY_SOLAR.plot(color="Red", ax=ax4)
    AVAIL_CAPACITY_ONWIND.plot(color="Green", ax=ax5)
    AVAIL_CAPACITY_OFFWIND.plot(color="Blue", ax=ax6)

    col1.pyplot(fig1)
    col2.pyplot(fig2)
    col3.pyplot(fig3)