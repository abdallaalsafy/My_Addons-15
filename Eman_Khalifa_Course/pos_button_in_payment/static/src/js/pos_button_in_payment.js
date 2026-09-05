odoo.define('pos_button_in_payment.CustompaymentButtonFile', function (require) {
    'use strict';

    const Registries = require("point_of_sale.Registries");
    const PaymentScreen = require("point_of_sale.PaymentScreen");

    const CustomPaymentButtonClss = (PaymentScreen) =>
    class extends PaymentScreen {
        IsCustomButton(){
            this.showPopup("ErrorPopup",{
                title: this.env._t("Custom Payment Button Clicked"),
                body: this.env._t("Welcome to OWL Payment Custom Button"),
            });
        }
    }
    Registries.Component.extend(PaymentScreen,CustomPaymentButtonClss);
    return CustomPaymentButtonClss;

    });