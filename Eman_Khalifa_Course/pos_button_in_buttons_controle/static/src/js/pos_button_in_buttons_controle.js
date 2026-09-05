odoo.define('pos_button_in_buttons_controle.CustomControlButtonFile', function (require) {
    'use strict';

    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");
    const ProductScreen = require("point_of_sale.ProductScreen");

    class CustomControlButtonClss extends PosComponent {
        onClick(){
            this.showPopup("ErrorPopup",{
                title: this.env._t("Custom Control Button Clicked"),
                body: this.env.pos.get_cashier().user_id[1],
            });
        }
    }
    CustomControlButtonClss.template = "CustomControlButtonTemp";
    ProductScreen.addControlButton({
        component:CustomControlButtonClss,
        condition(){return !!this.env.pos;},
    });
    Registries.Component.add(CustomControlButtonClss);

    });