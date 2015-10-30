module pong(
               input  logic [31:0] din,
               output logic [31:0] dout
               );

  always_comb begin
     dout <= {din[23:16], din[23:16], din[7:0], din[7:0]};
  end
endmodule
