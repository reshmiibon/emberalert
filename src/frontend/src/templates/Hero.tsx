import Image from 'next/image';
import Link from 'next/link';

import { Background } from '../background/Background';
import { Button } from '../button/Button';
import { HeroOneButton } from '../hero/HeroOneButton';
import { Section } from '../layout/Section';
import { NavbarTwoColumns } from '../navigation/NavbarTwoColumns';
import { Logo } from './Logo';

const Hero = () => (
  <>
    {/* White background for the top part, including Navbar */}
    <Background color="bg-white">
      <Section yPadding="py-6">
        <NavbarTwoColumns logo={<Logo xl />}>
          <li>
            <Link href="/map">Maps</Link>
          </li>
          <li>
            <Link href="/optin">Opt In</Link>
          </li>
        </NavbarTwoColumns>
      </Section>
    </Background>

    {/* Primary-100 background for the remaining sections */}
    <Background color="bg-primary-100">
      <Section yPadding="pt-20 pb-32">
        <HeroOneButton
          title={
            <>
              {'Know about wildfires in your area with\n'}
              <div style={{ display: 'flex', justifyContent: 'center' }}>
                <Image
                  src="/apple-touch-icon.png"
                  width={240}
                  height={240}
                  alt="logo"
                />
              </div>
            </>
          }
          description="Detection, Forecasting, and Alerting about Wildfires in your area."
          button={
            <Link href="/optin">
              <Button xl>OPT IN</Button>
            </Link>
          }
        />
      </Section>
    </Background>
  </>
);

export { Hero };
