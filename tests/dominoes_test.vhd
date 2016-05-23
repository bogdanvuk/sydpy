library ieee;
use ieee.std_logic_1164.all;

entity dominoes_test is
    port (
        trigger   :  in std_logic;
        last      : out std_logic
        );
end dominoes_test;

architecture rtl of dominoes_test is
    signal dominoes : std_logic_vector(31 downto 0) := (others => '0');
begin

    proc_dominoes: process(dominoes, trigger)
    begin
        dominoes(0) <= trigger;
        for i in 1 to 31 loop
            dominoes(i) <= dominoes(i-1);
        end loop;
        last <= dominoes(31);
    end process;

end rtl;
