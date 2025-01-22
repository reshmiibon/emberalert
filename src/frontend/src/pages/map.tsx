// opt in page
import Link from 'next/link';

import { Footer } from '@/templates/Footer';

import { Section } from '../layout/Section';
import { NavbarTwoColumns } from '../navigation/NavbarTwoColumns';
import { Logo } from '../templates/Logo';
import Map from '../templates/Map';

const Maps = () => (
  <>
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
    <Map />
    <Section>
      <div className="bg-white p-4 m-2 border-4 border-black" id="legend">Legend</div>
    </Section>
    <Footer />
  </>
);
export default Maps;
